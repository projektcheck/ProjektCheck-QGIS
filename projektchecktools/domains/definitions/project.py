from qgis.core import (QgsCoordinateReferenceSystem, QgsPointXY,
                       QgsCoordinateTransform, QgsProject,
                       QgsGeometry)
from datetime import datetime
import numpy as np
import shutil
import processing

from projektchecktools.base.project import ProjectManager
from projektchecktools.base.domain import Worker
from projektchecktools.domains.definitions.tables import (Teilflaechen,
                                                          Projektrahmendaten)
from projektchecktools.domains.traffic.tables import Connectors
from projektchecktools.domains.marketcompetition.tables import Centers
from projektchecktools.domains.constants import Nutzungsart
from projektchecktools.utils.utils import get_ags
from settings import settings


class ProjectInitialization(Worker):
    def __init__(self, project_name, area_layer, epsg, parent=None):
        super().__init__(parent=parent)
        self.project_name = project_name
        self.project_manager = ProjectManager()
        self.area_layer = area_layer
        self.epsg = epsg

    def work(self):
        try:
            return self.create_project()
        except Exception as e:
            if self.project_areas is not None:
                self.project_areas.workspace.close()
            self.project.remove()
            self.log('Projekt nach Fehler wieder entfernt.')
            raise e

    def create_project(self):
        self.project = self.project_manager.create_project(self.project_name)
        self.project_areas = None
        source_crs = self.area_layer.crs()
        target_crs = QgsCoordinateReferenceSystem(f'epsg:{self.epsg}')
        self.project_areas = Teilflaechen.features(project=self.project,
                                                   create=True)

        parameters = {
            'INPUT': self.area_layer,
            'DROP_Z_VALUES': True,
            'OUTPUT': 'memory:'
        }
        area_layer = processing.run(
            'native:dropmzvalues', parameters)['OUTPUT']

        layer_features = list(area_layer.getFeatures())

        self.log(f'Neues Projekt angelegt im Ordner {self.project.path}')
        self.set_progress(10)

        trans_geoms = []

        self.log(f'Füge {len(layer_features)} Fläche(n) hinzu...')
        tr = QgsCoordinateTransform(
            source_crs, target_crs, QgsProject.instance())
        if not layer_features:
            raise Exception('Es wurden keine Flächen im Eingangslayer gefunden')
        for area in layer_features:
            geom = area.geometry()
            geom.transform(tr)
            trans_geoms.append(geom)

        # gather additional information about areas

        basedata = self.project_manager.basedata
        ags_feats = get_ags(layer_features, basedata, source_crs=source_crs,
                            use_centroid=True)
        ags = [f.AGS_0 for f in ags_feats]
        gem_names = [f.GEN for f in ags_feats]
        gem_types = [f.Gemeindetyp for f in ags_feats]
        if len(np.unique(ags)) > 1:
            raise Exception("Die Teilflächen liegen nicht in "
                            "der selben Gemeinde")
        project_ags = ags[0]

        centroids = [geom.centroid().asPoint() for geom in trans_geoms]
        xs = [centroid.x() for centroid in centroids]
        ys = [centroid.y() for centroid in centroids]
        project_centroid = QgsPointXY(np.mean(xs), np.mean(ys))

        max_dist = getattr(settings, 'MAX_AREA_DISTANCE', None)

        self.set_progress(33)

        self.log(f'Überprüfe die Flächenlage...')
        if max_dist is not None and len(layer_features) > 1:
            distances = []
            for i in range(len(layer_features)):
                for j in range(i):
                    dist = np.linalg.norm(
                        np.subtract((xs[i], ys[i]), (xs[j], ys[j])))
                    distances.append(dist)
            if distances and max(distances) > max_dist:
                raise Exception("Der Abstand zwischen den Schwerpunkten der "
                                "Teilflächen darf nicht größer "
                                "als {} m sein!".format(max_dist))
        self.set_progress(50)

        traffic_connectors = Connectors.features(project=self.project,
                                                       create=True)

        self.log(f'Berechne Projektrahmendaten...')
        # create areas and connections to roads
        now = datetime.now()
        for i, feature in enumerate(layer_features):
            area = self.project_areas.add(
                nutzungsart=Nutzungsart.UNDEFINIERT.value,
                name=f'Flaeche_{i+1}',
                validiert=0,
                aufsiedlungsdauer=1,
                beginn_nutzung=now.year,
                ags_bkg=ags[i],
                gemeinde_name=gem_names[i],
                gemeinde_typ=gem_types[i],
                geom=trans_geoms[i]
            )
            traffic_connectors.add(
                id_teilflaeche=area.id,
                name_teilflaeche=area.name,
                geom=centroids[i]
            )
        self.set_progress(50)

        # general project data
        project_frame = Projektrahmendaten.features(project=self.project,
                                                    create=True)
        local_versions = self.project_manager.local_versions(
            settings.basedata_path)
        # newest local version
        basedata_version = local_versions[0]
        project_frame.add(
            ags=ags[0],
            gemeinde_name=gem_names[0],
            gemeinde_typ=gem_types[0],
            projekt_name=self.project.name,
            geom=project_centroid,
            datum=now.strftime("%d.%m.%Y"),
            basisdaten_version=basedata_version['version'],
            basisdaten_datum=basedata_version['date']
        )
        self.set_progress(60)

        # create selectable centers around the areas for the market competition
        # domain

        sk_radius = getattr(settings, 'PROJECT_RADIUS', 20000)
        self.log(f'Ermittle Gemeinden im Umkreis von {int(sk_radius/1000)} km...')

        workspace = basedata.get_workspace('Basisdaten_deutschland')
        vg_table = workspace.get_table('Verwaltungsgemeinschaften')
        buffer = QgsGeometry.fromPointXY(
            QgsPointXY(*project_centroid)).buffer(sk_radius, 20)
        vg_table.spatial_filter(buffer.asWkt())
        centers = Centers.features(project=self.project, create=True)
        rs_list = []
        for row in vg_table:
            centers.add(
                name=row['GEN'],
                rs=row['RS'],
                geom=row['geom'],
                # -1 indicates that it is a vg for selection and output only
                nutzerdefiniert=-1
            )
            rs_list.append(row['RS'])

        project_rs = None
        gem_table = workspace.get_table('bkg_gemeinden')
        for row in gem_table:
            cut_rs = row['RS'][:9]
            ags = row['AGS']
            if cut_rs in rs_list:
                if ags == project_ags:
                    project_rs = cut_rs
                centers.add(
                    name=row['GEN'],
                    rs=cut_rs,
                    ags=ags,
                    geom=row['geom'],
                    # 0 indicates gemeinden, for calculations only
                    nutzerdefiniert=0
                )

        # preselect the VG the project is in
        if project_rs:
            project_vg = centers.get(rs=project_rs, nutzerdefiniert=-1)
            project_vg.auswahl = -1
            project_vg.save()

        self.set_progress(100)

        return self.project


class CloneProject(Worker):
    def __init__(self, project_name, project, parent=None):
        super().__init__(parent=parent)
        self.project_name = project_name
        self.origin_project = project
        self.project_manager = ProjectManager()

    def work(self):

        cloned_project = self.project_manager.create_project(
            self.project_name, create_folder=False)
        self.log('Kopiere Projektordner...')

        # copy template folder
        try:
            shutil.copytree(self.origin_project.path, cloned_project.path)
        except Exception as e:
            self.error.emit(str(e))
            self.project_manager.remove_project(self.project_name)
            return
        self.log('Neues Projekt erfolgreich angelegt '
                 f'unter {cloned_project.path}')
        return cloned_project