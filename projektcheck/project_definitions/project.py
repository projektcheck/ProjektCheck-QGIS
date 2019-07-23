from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject)
from datetime import datetime

from projektcheck.project_definitions.projecttables import Areas
from projektcheck.project_definitions.constants import Nutzungsart

def init_project(project, area_layer, epsg):
    source_crs = area_layer.crs()
    target_crs = QgsCoordinateReferenceSystem(epsg)
    features = Areas.features(project=project, create=True)
    for i, area in enumerate(area_layer.getFeatures()):
        tr = QgsCoordinateTransform(
            source_crs, target_crs, QgsProject.instance())
        geom = area.geometry()
        geom.transform(tr)
        features.add(
            nutzungsart=Nutzungsart.UNDEFINIERT.value,
            name=f'Flaeche_{i+1}',
            validiert=0,
            aufsiedlungsdauer=1,
            nutzungsdauer=datetime.now().year,
            geom=geom
        )
