# -*- coding: utf-8 -*-
import processing
import os
from qgis.core import QgsRasterLayer
from projektchecktools.utils.spatial import create_layer

from projektchecktools.domains.definitions.tables import (Teilflaechen,
                                                          Projektrahmendaten)
from projektchecktools.domains.municipaltaxrevenue.tables import (
    Gemeinden, EinwohnerWanderung)
from projektchecktools.base.domain import Worker


class Migration(Worker):
    _param_projectname = 'projectname'
    rings = [1500, 2500, 3500, 4500, 6500, 8500, 11500, 14500, 18500, 25000]

    def __init__(self, project, parent=None):
        super().__init__(parent=parent)
        self.project = project
        self.areas = Teilflaechen.features(project=project)
        self.gemeinden = Gemeinden.features(project=project)
        self.project_frame = Projektrahmendaten.features()[0]
        self.wanderung_ew = EinwohnerWanderung.features(project=project)

    def work(self):
        self.zensus_layer = self.get_zensus_layer()
        self.wanderung_ew.table.truncate()

        for i in range(len(self.rings)):
            inner_distance = 0 if i == 0 else self.rings[i-1]
            outer_distance = self.rings[i]
            ew_ags = self.get_ring_ew(inner_distance, outer_distance)

        project_ags = self.project_frame.ags
        for gemeinde in self.gemeinden:
            zuzug = sum_ew if gemeinde.AGS == project_ags else 0
            self.wanderung_einw.add(zuzug=zuzug)

    def get_ring_ew(self, inner_distance, outer_distance):
        pass

    def get_zensus_layer(self):
        epsg = self.project.settings.EPSG
        zensus_file = os.path.join(self.project.basedata.base_path,
                                   self.project.settings.ZENSUS_100_FILE)
        raster_layer = QgsRasterLayer(zensus_file)

        parameters = {
            'INPUT_RASTER':raster_layer,
            'RASTER_BAND': 1,
            'FIELD_NAME': 'value',
            'OUTPUT': 'memory:'
        }
        point_layer = processing.run(
            'native:pixelstopoints', parameters)['OUTPUT']

        overlay = create_layer(self.gemeinden, 'Polygon', fields=['ags'],
                               name='overlay', epsg=epsg,
                               target_epsg=raster_layer.crs().postgisSrid())

        parameters = {
            'INPUT': point_layer,
            'OVERLAY': overlay,
            'OUTPUT': 'memory:'
        }
        clipped_layer = processing.run('native:clip', parameters)['OUTPUT']

        parameters = {
            'INPUT': clipped_layer,
            'OVERLAY': overlay,
            'OUTPUT': 'memory:'
        }
        clipped_w_ags = processing.run(
            'native:intersection', parameters)['OUTPUT']

        return clipped_w_ags