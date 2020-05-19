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
import pandas as pd


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
        #p = self.zensus_layer.dataProvider()
        #p.truncate()
        if not self.zensus_layer.isValid() or len(self.zensus_layer) == 0:
            self.zensus_layer = self.create_zensus_rings()
        else:
            self.log('Siedlungszellen bereits vorhanden, '
                     'Berechnung wird übersprungen')
        self.set_progress(40)
        self.log('Berechne Wanderungsanteile...')
        self.wanderung_ew.table.truncate()
        columns = [f.name() for f in self.zensus_layer.fields()]
        rows = [f.attributes() for f in self.zensus_layer.getFeatures()]
        df_zensus = pd.DataFrame.from_records(rows, columns=columns)
        #df_zensus.rename(columns={'value': 'ew',}, inplace=True)
        df_wichtung = self.project.basedata.get_table(
            'Wanderung_Entfernungswichtung', 'Einnahmen').to_pandas(
                columns=['Distance', 'Wichtung_Wohnen'])
        df_wichtung.rename(columns={'Distance': 'ring'}, inplace=True)
        df_merged = df_zensus.merge(df_wichtung, on='ring', how='left')
        df_merged['ew_wichtet'] = df_merged['ew'] * df_merged['Wichtung_Wohnen']
        grouped = df_merged.groupby('AGS')
        ew_wichtet_ags = grouped['ew_wichtet'].sum()
        anteil_ags = ew_wichtet_ags / ew_wichtet_ags.sum()

        self.set_progress(50)
        project_ags = self.project_frame.ags
        zuzug_project = sum(self.areas.values('ew'))
        randsummen = self.project.basedata.get_table(
            'Wanderung_Randsummen', 'Einnahmen').features()
        factor = randsummen.get(IDWanderungstyp=1).Anteil_Wohnen
        for AGS, anteil in anteil_ags.items():
            zuzug = zuzug_project if AGS == project_ags else 0
            gemeinde = self.gemeinden.get(AGS=AGS)
            self.wanderung_ew.add(
                zuzug=zuzug,
                AGS=AGS,
                wanderungs_anteil=anteil,
                fixed=False,
                geom=gemeinde.geom
            )
        self.set_progress(80)
        self.log('Berechne Wanderungssaldi...')
        df_result = self.calculate_saldi(
            self, self.wanderung_ew.to_pandas(), factor, project_ags)
        self.wanderung_ew.update_pandas(df_result)

    @staticmethod
    def calculate_saldi(self, df_wanderung_ew, wanderungs_factor, project_ags,
                        decimals=2):
        project_row = df_wanderung_ew[df_wanderung_ew['AGS']==project_ags]
        zuzug = project_row['zuzug'].values[0]
        fortzug_25 = zuzug * wanderungs_factor
        fixed_idx = df_wanderung_ew['fixed'] == True
        variable_idx = df_wanderung_ew['fixed'] == False
        variable_rows = df_wanderung_ew[variable_idx]
        fortzug_fixed = df_wanderung_ew[fixed_idx]['fortzug'].sum()
        wanderungsanteil_variable = variable_rows['wanderungs_anteil'].sum()
        fortzug_pro_anteil = ((fortzug_25 - fortzug_fixed) /
                              wanderungsanteil_variable)
        df_wanderung_ew.loc[variable_idx, 'fortzug'] = (
            variable_rows['wanderungs_anteil'] * fortzug_pro_anteil)
        # reload rows, have been updated
        variable_rows = df_wanderung_ew[variable_idx]
        df_wanderung_ew.loc[variable_idx, 'saldo'] = (variable_rows['zuzug'] -
                                                      variable_rows['fortzug'])
        return df_wanderung_ew

    def create_zensus_rings(self):
        self.log('Extrahiere Siedlungszellen aus Zensusdaten...')
        epsg = self.project.settings.EPSG
        zensus_file = os.path.join(self.project.basedata.base_path,
                                   self.project.settings.ZENSUS_100_FILE)

        bbox = get_bbox(self.gemeinden.table)
        clipped_raster = clip_raster(zensus_file, bbox)

        raster_layer = QgsRasterLayer(clipped_raster)

        parameters = {
            'INPUT_RASTER':raster_layer,
            'RASTER_BAND': 1,
            'FIELD_NAME': 'ew',
            'OUTPUT': 'memory:'
        }

        point_layer = processing.run(
            'native:pixelstopoints', parameters)['OUTPUT']
        point_layer.setSubsetString('ew>0')

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

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        options.layerName = 'zensus_rings'
        QgsVectorFileWriter.writeAsVectorFormat(
            clipped_w_ags, self.gemeinden.workspace.path, options)

        return clipped_w_ags
