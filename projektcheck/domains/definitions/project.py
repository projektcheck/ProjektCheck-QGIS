from qgis.core import (QgsCoordinateReferenceSystem, QgsPointXY,
                       QgsCoordinateTransform, QgsProject,
                       QgsGeometry)
from datetime import datetime
import numpy as np

from projektcheck.base import Worker, ProjectManager
from projektcheck.domains.definitions.tables import Areas, ProjectData
from projektcheck.domains.traffic.tables import TrafficConnector
from projektcheck.domains.marketcompetition.tables import Centers
from projektcheck.domains.constants import Nutzungsart
from projektcheck.utils.utils import get_ags
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
        target_crs = QgsCoordinateReferenceSystem(self.epsg)
        self.project_areas = Areas.features(project=self.project, create=True)
        layer_features = list(self.area_layer.getFeatures())

        self.log(f'Neues Projekt angelegt im Ordner {self.project.path}')
        self.set_progress(10)

        trans_geoms = []

        self.log(f'Füge {len(layer_features)} Flächen hinzu...')
        tr = QgsCoordinateTransform(
            source_crs, target_crs, QgsProject.instance())
        for area in layer_features:
            geom = area.geometry()
            geom.transform(tr)
            trans_geoms.append(geom)

        # gather additional information about areas

        ags_feats = get_ags(layer_features, source_crs=source_crs)
        ags = [f.AGS_0 for f in ags_feats]
        gem_names = [f.GEN for f in ags_feats]
        gem_types = [f.Gemeindetyp for f in ags_feats]
        if len(np.unique(ags)) > 1:
            raise Exception("Die Teilflächen liegen nicht in "
                            "der selben Gemeinde")

        centroids = [geom.centroid().asPoint() for geom in trans_geoms]
        xs = [centroid.x() for centroid in centroids]
        ys = [centroid.y() for centroid in centroids]
        project_centroid = (np.mean(xs), np.mean(ys))

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

        traffic_connectors = TrafficConnector.features(project=self.project,
                                                       create=True)

        self.log(f'Berechne Projektrahmendaten...')
        # create areas and connections to roads
        for i, feature in enumerate(layer_features):
            area = self.project_areas.add(
                nutzungsart=Nutzungsart.UNDEFINIERT.value,
                name=f'Flaeche_{i+1}',
                validiert=0,
                aufsiedlungsdauer=1,
                nutzungsdauer=datetime.now().year,
                ags_bkg=ags[i],
                gemeinde_name=gem_names[i],
                geom=trans_geoms[i]
            )
            traffic_connectors.add(
                id_teilflaeche=area.id,
                name_teilflaeche=area.name,
                geom=centroids[i]
            )
        self.set_progress(66)

        # general project data
        project_frame = ProjectData.features(project=self.project, create=True)
        project_frame.add(
            ags=ags[0],
            gemeinde_name=gem_names[0],
            gemeinde_typ=gem_types[0],
            projekt_name=self.project.name
        )
        self.set_progress(80)

        # create selectable centers around the areas for the market competition
        # domain

        sk_radius = getattr(settings, 'PROJECT_RADIUS', 20000)
        self.log(f'Ermittle Gemeinden im Umkreis von {sk_radius/1000} km...')

        basedata = settings.BASEDATA.get_workspace('Basisdaten_deutschland')
        vg_table = basedata.get_table('Verwaltungsgemeinschaften')
        buffer = QgsGeometry.fromPointXY(
            QgsPointXY(*project_centroid)).buffer(sk_radius, 20)
        vg_table.spatial_filter(buffer.asWkt())
        centers = Centers.features(project=self.project, create=True)
        for row in vg_table:
            centers.add(
                name=row['GEN'],
                rs=row['RS'],
                geom=row['geom'],
                # -1 indicates that it is a vg for selection and output only
                nutzerdefiniert=-1
            )

        self.set_progress(100)

        return self.project


