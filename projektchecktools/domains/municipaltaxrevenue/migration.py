# -*- coding: utf-8 -*-
import processing
import os
from qgis.core import (QgsRasterLayer, QgsVectorLayer, QgsFeature,
                       QgsVectorFileWriter, QgsField)
from qgis.PyQt.Qt import QVariant

from projektchecktools.utils.spatial import create_layer
from projektchecktools.domains.definitions.tables import (Teilflaechen,
                                                          Projektrahmendaten)
from projektchecktools.domains.municipaltaxrevenue.tables import (
    Gemeinden, EinwohnerWanderung)
from projektchecktools.base.domain import Worker
from projektchecktools.utils.spatial import clip_raster, get_bbox
import time


class Migration(Worker):
    _param_projectname = 'projectname'
    rings = [1500, 2500, 3500, 4500, 6500, 8500, 11500, 14500, 18500, 25000]

    def __init__(self, project, parent=None):
        super().__init__(parent=parent)
        self.project = project
        self.areas = Teilflaechen.features(project=project)
        self.gemeinden = Gemeinden.features(project=project)
        self.zensus_layer = QgsVectorLayer(f'{self.gemeinden.workspace.path}'
                            '|layername=zensus_rings')
        self.project_frame = Projektrahmendaten.features()[0]
        self.wanderung_ew = EinwohnerWanderung.features(project=project)

    def work(self):
        p = self.zensus_layer.dataProvider()
        p.truncate()
        if not self.zensus_layer.isValid() or len(self.zensus_layer) == 0:
            self.zensus_layer = self.create_zensus_rings()
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
        print()

    def create_zensus_rings(self):
        self.log('Extrahiere Siedlungszellen aus Zensusdaten...')
        epsg = self.project.settings.EPSG
        zensus_file = os.path.join(self.project.basedata.base_path,
                                   self.project.settings.ZENSUS_100_FILE)

        bbox = get_bbox(self.gemeinden.table)
        clipped_raster = clip_raster(zensus_file, bbox)

        raster_layer = QgsRasterLayer(clipped_raster)

        start = time.time()
        parameters = {
            'INPUT_RASTER':raster_layer,
            'RASTER_BAND': 1,
            'FIELD_NAME': 'value',
            'OUTPUT': 'memory:'
        }

        point_layer = processing.run(
            'native:pixelstopoints', parameters)['OUTPUT']
        point_layer.setSubsetString('value>0')

        parameters = {
            'INPUT': point_layer,
            'TARGET_CRS': f'EPSG:{epsg}',
            'OUTPUT': 'memory:'
        }

        point_proj = processing.run(
            'native:reprojectlayer', parameters)['OUTPUT']

        # clip with max distance from project area
        buffer_geom = self.project_frame.geom.buffer(self.rings[-1], 100)
        buffer = QgsFeature()
        buffer.setGeometry(buffer_geom)
        overlay = QgsVectorLayer(f'Polygon?crs=EPSG:{epsg}',
                                 'buffer', 'memory')
        overlay.dataProvider().addFeature(buffer)
        parameters = {
            'INPUT': point_proj,
            'OVERLAY': overlay,
            'OUTPUT': 'memory:'
        }
        clipped_layer = processing.run('native:clip', parameters)['OUTPUT']

        # intersect with rings to get distance bin
        ring_layer = QgsVectorLayer(f'Polygon?crs=EPSG:{epsg}', 'rings',
                                    'memory')
        pr = ring_layer.dataProvider()
        pr.addAttributes([QgsField('ring', QVariant.Int)])
        ring_layer.updateFields()
        center = self.project_frame.geom
        prev_outer_circle = None
        for distance in self.rings:
            ring = QgsFeature()
            outer_circle = center.buffer(distance, 100)
            if prev_outer_circle is not None:
                geom = outer_circle.difference(prev_outer_circle)
            else:
                geom = outer_circle
            prev_outer_circle = outer_circle
            ring.setGeometry(geom)
            ring.setAttributes([distance])
            pr.addFeature(ring)

        parameters = {
            'INPUT': clipped_layer,
            'OVERLAY': ring_layer,
            'OUTPUT': 'memory:'
        }
        self.log('Verschneide Siedlungszellen mit Entfernungsringen '
                 'und Gemeinden...')
        clipped_w_distance = processing.run(
            'native:intersection', parameters)['OUTPUT']

        # intersect with "gemeinden" to add AGS to cells
        gem_overlay = create_layer(self.gemeinden, 'Polygon', fields=['AGS'],
                                   name='overlay', epsg=epsg)
        parameters = {
            'INPUT': clipped_w_distance,
            'OVERLAY': gem_overlay,
            'OUTPUT': 'memory:'
        }
        self.log('Verschneide Siedlungszellen mit Entfernungsringen '
                 'und Gemeinden...')
        clipped_w_ags = processing.run(
            'native:intersection', parameters)['OUTPUT']

        end = time.time() - start
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        options.layerName = 'zensus_rings'
        QgsVectorFileWriter.writeAsVectorFormat(
            clipped_w_ags, self.gemeinden.workspace.path, options)
