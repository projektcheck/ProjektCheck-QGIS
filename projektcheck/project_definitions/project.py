from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject)
from datetime import datetime

from projektcheck.project_definitions.projecttables import Areas

def init_project(project, area_layer, epsg):
    source_crs = area_layer.crs()
    target_crs = QgsCoordinateReferenceSystem(epsg)
    tfl_table = Areas.get(project=project)
    for i, feature in enumerate(area_layer.getFeatures()):
        row = {
            'id': i + 1,
            'nutzungsart': 0,
            'name': f'Flaeche_{i+1}',
            'validated': 0,
            'aufsiedlungsdauer': 1,
            'nutzungsdauer': datetime.now().year,
        }
        tr = QgsCoordinateTransform(
            source_crs, target_crs, QgsProject.instance())
        geom = feature.geometry()
        geom.transform(tr)
        tfl_table.add(row, geom=geom)
