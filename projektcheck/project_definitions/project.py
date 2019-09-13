from qgis.core import (QgsCoordinateReferenceSystem, QgsPointXY,
                       QgsCoordinateTransform, QgsProject,
                       QgsGeometry)
from datetime import datetime
import numpy as np

from projektcheck.project_definitions.definitiontables import Areas, Framework
from projektcheck.project_definitions.traffictables import TrafficConnector
from projektcheck.project_definitions.markettables import Centers
from projektcheck.project_definitions.constants import Nutzungsart
from projektcheck.project_definitions.utils import get_ags
from settings import settings

def init_project(project, area_layer, epsg):
    source_crs = area_layer.crs()
    target_crs = QgsCoordinateReferenceSystem(epsg)
    project_areas = Areas.features(project=project, create=True)
    layer_features = list(area_layer.getFeatures())

    trans_geoms = []
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
        raise Exception("Die Teilflächen liegen nicht in der selben Gemeinde")

    centroids = [geom.centroid().asPoint() for geom in trans_geoms]
    xs = [centroid.x() for centroid in centroids]
    ys = [centroid.y() for centroid in centroids]
    project_centroid = (np.mean(xs), np.mean(ys))

    max_dist = getattr(settings, 'MAX_AREA_DISTANCE', None)
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

    traffic_connectors = TrafficConnector.features(project=project, create=True)

    # create areas and connections to roads
    for i, feature in enumerate(layer_features):
        area = project_areas.add(
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

    # general project data
    project_frame = Framework.features(project=project, create=True)
    project_frame.add(
        ags=ags[0],
        gemeinde_name=gem_names[0],
        gemeinde_typ=gem_types[0],
        projekt_name=project.name
    )

    # create selectable centers around the areas for the market competition
    # domain

    sk_radius = getattr(settings, 'PROJECT_RADIUS', 20000)
    basedata = settings.BASEDATA.get_workspace('Basisdaten_deutschland')
    vg_table = basedata.get_table('Verwaltungsgemeinschaften')
    buffer = QgsGeometry.fromPointXY(
        QgsPointXY(*project_centroid)).buffer(sk_radius, 20)
    vg_table.spatial_filter(buffer.asWkt())
    centers = Centers.features(project=project, create=True)
    for row in vg_table:
        centers.add(
            name=row['GEN'],
            rs=row['RS'],
            geom=row['geom'],
            # -1 indicates that it is a vg for selection and output only
            nutzerdefiniert=-1
        )


