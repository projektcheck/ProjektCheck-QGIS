from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject)
from datetime import datetime
import numpy as np

from projektcheck.project_definitions.projecttables import Areas
from projektcheck.project_definitions.constants import Nutzungsart
from projektcheck.project_definitions.utils import get_ags
from settings import settings

def init_project(project, area_layer, epsg):
    source_crs = area_layer.crs()
    target_crs = QgsCoordinateReferenceSystem(epsg)
    project_features = Areas.features(project=project, create=True)
    layer_features = list(area_layer.getFeatures())

    trans_geoms = []
    tr = QgsCoordinateTransform(
        source_crs, target_crs, QgsProject.instance())
    for area in layer_features:
        geom = area.geometry()
        geom.transform(tr)
        trans_geoms.append(geom)

    ags = get_ags(layer_features, source_crs=source_crs)
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

    for i, area in enumerate(layer_features):
        project_features.add(
            nutzungsart=Nutzungsart.UNDEFINIERT.value,
            name=f'Flaeche_{i+1}',
            validiert=0,
            aufsiedlungsdauer=1,
            nutzungsdauer=datetime.now().year,
            geom=trans_geoms[i]
        )



def get_gemeinde(features, source_crs):
    ags = get_ags(features, source_crs=source_crs)
    max_dist = getattr(settings, 'MAX_AREA_DISTANCE', None)

    if max_dist is not None:

    """Verschneide Teilflächen mit Gemeinde"""
    # to do (Stefaan)
    arcpy.SetProgressorLabel('Verschneide Teilflächen mit Gemeinde')
    arcpy.SetProgressorPosition(10)

    # calculate Gauß-Krüger-Coordinates and append them to tfl
    arcpy.AddGeometryAttributes_management(
        Input_Features=tfl, Geometry_Properties="CENTROID_INSIDE")

    # Check if the distances between the centroids is smaller than max_dist
    toolbox = self.parent_tbx
    XY_INSIDE = toolbox.query_table("Teilflaechen_Plangebiet",
                                    ['INSIDE_X', 'INSIDE_Y'])
    INSIDE_X = [row[0] for row in XY_INSIDE]
    INSIDE_Y = [row[1] for row in XY_INSIDE]
    self._project_centroid = (np.mean(INSIDE_X), np.mean(INSIDE_Y))
    distances = []
    if len(XY_INSIDE) > 1:
        for i in range(len(XY_INSIDE)):
            for j in range(i):
                dist = np.linalg.norm(np.subtract(XY_INSIDE[i], XY_INSIDE[j]))
                distances.append(dist)
        if distances and max(distances) > max_dist:
            raise Exception("Der Abstand zwischen den Schwerpunkten der "
                            "Teilflächen darf nicht größer "
                            "als {} m sein!".format(max_dist))

    # get AGS and Gemeindename and check if AGS is unique
    ags_gen = get_ags(tfl, id_column)
    ags_project = [ID[0] for ID in ags_gen.values()]
    gen_project =  [ID[1] for ID in ags_gen.values()]
    if len(np.unique(ags_project)) != 1:
        raise Exception("Die Teilflächen müssen in der selben Gemeinde"
                        "liegen")

    return ags_project[0], gen_project[0]
