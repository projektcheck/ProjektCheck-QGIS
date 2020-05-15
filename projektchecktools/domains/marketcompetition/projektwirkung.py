# -*- coding: utf-8 -*-
import os
import pandas as pd
import json
import numpy as np
import pandas as pd
import gc
from collections import Counter
import processing
from qgis.core import (QgsCoordinateTransform, QgsProject, QgsVectorLayer,
                       QgsCoordinateReferenceSystem, QgsRasterLayer)

from projektchecktools.domains.marketcompetition.tables import (
    Centers, Markets, MarketCellRelations, Settings, SettlementCells)
from projektchecktools.domains.definitions.tables import Teilflaechen
from projektchecktools.domains.marketcompetition.routing_distances import (
    DistanceRouting)
from projektchecktools.utils.spatial import Point, create_layer, intersect
from projektchecktools.base.domain import Worker
from projektchecktools.domains.marketcompetition.sales import Sales

DEBUG = False


class Projektwirkung(Worker):
    _param_projectname = 'projectname'

    def __init__(self, project, recalculate=False, settlement_buffer=3000,
                 markets_buffer=6000, parent=None):
        super().__init__(parent=parent)
        self.areas = Teilflaechen.features(project=project)
        self.markets = Markets.features(project=project)
        self.centers = Centers.features(project=project)
        self.relations = MarketCellRelations.features(project=project,
                                                    create=True)
        self.cells = SettlementCells.features(project=project, create=True)
        self.settings = Settings.features(project=project, create=True)
        self.project = project
        self.recalculate = recalculate
        self.markets_buffer = markets_buffer
        self.settlement_buffer = settlement_buffer

    def validate_inputs(self):
        df_markets = self.markets.to_pandas()
        id_nullfall = df_markets['id_betriebstyp_nullfall']
        id_planfall = df_markets['id_betriebstyp_planfall']
        planfall_idx = np.logical_and((id_nullfall != id_planfall),
                                      (id_planfall > 0))
        planfall_markets = df_markets[planfall_idx]
        unset_markets = planfall_markets[planfall_markets['id_kette'] == 0]
        if len(unset_markets) > 0:
            m_str = ''
            for idx, market in unset_markets.iterrows():
                m_str += f'  - {market["name"]}\n'
            msg = ('Bei folgenden geplanten Märkten ist der Anbieter zur Zeit '
                   f'noch unbekannt:\n{m_str}\n'
                   'Bitte setzen sie vor der Berechnung die Anbieter für alle '
                   'geplanten Märkte')
            return False, msg
        return True, ''

    def work(self):
        # check the settings of last calculation
        selected_vg = self.centers.filter(auswahl__ne=0, nutzerdefiniert=-1)
        selected_rs = [v.rs for v in selected_vg]
        gemeinden = self.centers.filter(nutzerdefiniert=0)
        for gem in gemeinden:
            gem.auswahl = 1 if gem.rs in selected_rs else 0
            gem.save()
        gemeinden_in_auswahl = gemeinden.filter(auswahl=1)
        cur_ags = [c.ags for c in gemeinden_in_auswahl]

        if len(self.settings) == 0:
            # force recalc., because settings are empty (no calc. before)
            self.settings.add(betrachtungsraum=','.join(cur_ags))
            self.recalculate = True
        else:
            settings = self.settings[0]
            prev_ags = settings.betrachtungsraum.split(',')
            if Counter(cur_ags) != Counter(prev_ags):
                self.log('Der gepufferte Betrachtungsraum hat sich seit der '
                         'letzten Berechnung geändert. Neuberechnung der '
                         'Siedlungszellen und Distanzen wird ausgeführt.')
                self.recalculate = True
                settings.betrachtungsraum = ','.join(cur_ags)

        # empty result tables (empty indicates need of recalculation later on)
        if self.recalculate:
            self.relations.table.truncate()
            self.cells.table.truncate()

        defaults = self.project.basedata.get_table(
            'Grundeinstellungen',
            workspace='Standortkonkurrenz_Supermaerkte').features()
        default_kk_index = defaults.get(Info='KK je Einwohner default').Wert
        base_kk = defaults.get(Info='Kaufkraft pro Person').Wert

        sz_count = len(self.cells)
        if sz_count == 0:
            # calculate cells with inhabitants (incl. 'teilflaechen')
            self.calculate_zensus(gemeinden_in_auswahl,
                                  default_kk_index, base_kk)
        else:
            self.log('Siedlungszellen bereits vorhanden, '
                     'Berechnung wird übersprungen')
        self.set_progress(20)
        self.log(u'Aktualisiere Siedlungszellen der Teilflächen...')
        self.update_areas(default_kk_index, base_kk)

        self.set_progress(25)
        self.log(u'Berechne Erreichbarkeiten der Märkte...')
        self.calculate_distances(progress_start=25, progress_end=60)

        self.set_progress(60)
        self.log(u'Lade Eingangsdaten für die nachfolgenden '
                 u'Berechnungen...')
        # reload markets
        df_markets = self.markets.to_pandas().rename(columns={'fid': 'id'})
        df_relations = self.relations.to_pandas()
        df_cells = self.cells.to_pandas().rename(columns={'fid': 'id'})

        sales = Sales(self.project.basedata, df_relations, df_markets, df_cells,
                      debug=DEBUG)
        self.set_progress(70)
        self.log('Berechne Nullfall...')
        kk_nullfall = sales.calculate_nullfall()
        self.log('Berechne Planfall...')
        kk_planfall = sales.calculate_planfall()
        self.set_progress(85)
        self.log('Berechne Kenngrößen...')
        self.sales_to_db(kk_nullfall, kk_planfall)
        self.log('Werte Ergebnisse auf Verwaltungsgemeinschaftsebene und '
                 'für die Zentren aus...')
        self.update_centers()

    def calculate_zensus(self, gemeinden, default_kk_index, base_kk):
        self.log('Extrahiere Siedlungszellen aus Zensusdaten...')
        epsg = self.project.settings.EPSG
        """
        return the centroids of the zensus cells as points inside the
        given area
        """
        zensus_file = os.path.join(self.project.basedata.base_path,
                                   self.project.settings.ZENSUS_FILE)
        raster_layer = QgsRasterLayer(zensus_file)

        parameters = {
            'INPUT_RASTER':raster_layer,
            'RASTER_BAND': 1,
            'FIELD_NAME': 'value',
            'OUTPUT': 'memory:'
        }
        point_layer = processing.run(
            'native:pixelstopoints', parameters)['OUTPUT']

        overlay = create_layer(gemeinden, 'Polygon', fields=['ags'],
                               name='overlay', epsg=epsg,
                               target_epsg=raster_layer.crs().postgisSrid())

        #clip_tmp = tempfile.NamedTemporaryFile(suffix='.gpkg').name
        parameters = {
            'INPUT': point_layer,
            'OVERLAY': overlay,
            'OUTPUT': 'memory:'
        }
        clipped_layer = processing.run(
            'native:clip', parameters)['OUTPUT']

        parameters = {
            'INPUT': clipped_layer,
            'OVERLAY': overlay,
            'OUTPUT': 'memory:'
        }
        clipped_w_ags = processing.run(
            'native:intersection', parameters)['OUTPUT']

        self.log('Schreibe Siedlungszellen in Datenbank...')
        tr = QgsCoordinateTransform(
            clipped_w_ags.crs(), QgsCoordinateReferenceSystem(epsg),
            QgsProject.instance()
        )

        ags_list = [g.ags for g in gemeinden]
        gem_acc = dict([(a, [0, 0]) for a in ags_list])

        for feature in clipped_w_ags.getFeatures():
            ew = feature.attribute('VALUE')
            if ew <= 0:
                continue
            # for some reason all geometries are MultiPoint with length 1
            geom = feature.geometry()
            geom.transform(tr)
            point = geom.asMultiPoint()[0]
            ags = feature.attribute('ags')
            # take default kk_index only atm (there is a table (KK2015) with
            # indices in the basedata though)
            kk_index = default_kk_index
            kk = ew * base_kk * kk_index / 100
            self.cells.add(
                ew=ew,
                kk_index=kk_index,
                kk=kk,
                id_teilflaeche=-1,
                in_auswahl=True,
                geom=point,
                ags=ags
            )
            # accumulate einwohner and kaufkraft
            acc = gem_acc[ags]
            acc[0] += ew
            acc[1] += kk

        for ags, (ew, kk) in gem_acc.items():
            gem = self.centers.get(ags=ags)
            gem.ew = ew
            gem.kk = kk
            gem.save()

    def update_areas(self, default_kk_index, base_kk):
        for area in self.areas:
            cell = self.cells.get(id_teilflaeche=area.id)
            if not cell:
                cell = self.cells.add(
                    id_teilflaeche=area.id,
                    ew=area.ew,
                    kk_index=default_kk_index,
                    in_auswahl=True,
                    geom=area.geom.centroid(),
                    ags=area.ags_bkg
                )
            cell.kk = area.ew * base_kk * cell.kk_index / 100
            cell.save()

    def get_bbox(self, table):
        layer = QgsVectorLayer(f'{table.workspace.path}|layername={table.name}')
        ex = layer.extent()
        epsg = layer.crs().postgisSrid()
        bbox = (Point(ex.xMinimum(), ex.yMinimum(), epsg=epsg),
                Point(ex.xMaximum(), ex.yMaximum(), epsg=epsg))
        return bbox

    def calculate_distances(self, progress_start=0, progress_end=100):
        '''calculate distances between settlement points and markets and
        write them to the database'''

        # calculate bounding box
        bbox = self.get_bbox(self.cells.table)
        epsg = self.project.settings.EPSG
        routing = DistanceRouting(target_epsg=epsg, resolution=300)
        destinations = []
        for cell in self.cells:
            pnt = cell.geom.asPoint()
            destinations.append(Point(pnt.x(), pnt.y(), id=cell.id, epsg=epsg))
        already_calculated = np.unique(self.relations.values('id_markt'))
        self.markets.filter()
        n_markets = len(self.markets)
        progress_step = (progress_end - progress_start) / n_markets
        i = 1
        for market in self.markets:
            self.log(f' - {market.name} ({i}/{n_markets})')
            if market.id not in already_calculated:
                self.log('&nbsp;&nbsp;wird berechnet')
                pnt = market.geom.asPoint()
                origin = Point(pnt.x(), pnt.y(), id=market.id, epsg=epsg)
                #try:
                distances, beelines = routing.get_distances(
                    origin, destinations, bbox)
                #except Exception as e:
                    #self.error.emit(str(e))
                    #print(str(e))
                    #continue
                self.distances_to_db(market.id, destinations, distances,
                                     beelines)
            else:
                self.log('&nbsp;&nbsp;bereits berechnet, wird übersprungen')
            self.set_progress(progress_start + (i * progress_step))
            i += 1

    def sales_to_db(self, kk_nullfall, kk_planfall):
        '''store the sales matrices in database'''
        # sum up sales join them on index to dataframe, replace missing entries
        # (e.g. no entries for planned markets in nullfall -> sales = 0)
        sales_nullfall = kk_nullfall.sum(axis=1)
        sales_planfall = kk_planfall.sum(axis=1)
        df_sales_null = pd.DataFrame(
            sales_nullfall, columns=['umsatz_nullfall'])
        df_sales_plan = pd.DataFrame(
            sales_planfall, columns=['umsatz_planfall'])
        df_sales = df_sales_null.join(df_sales_plan, how='outer')
        df_sales.fillna(0, inplace=True)
        df_sales['fid'] = df_sales.index
        df_sales['umsatz_differenz'] = (
            (df_sales['umsatz_planfall'] /
             df_sales['umsatz_nullfall']) * 100 - 100)
        df_sales.fillna(0, inplace=True)

        self.markets.update_pandas(df_sales)
        market_ids = [m.id for m in self.markets]

        # invert the pivoted tables
        kk_nullfall['id_markt'] = kk_nullfall.index
        kk_planfall['id_markt'] = kk_planfall.index
        df_nullfall = pd.melt(kk_nullfall,
                              value_name='kk_strom_nullfall',
                              id_vars='id_markt')
        df_planfall = pd.melt(kk_planfall,
                              value_name='kk_strom_planfall',
                              id_vars='id_markt')

        # join the results to the cell table, only relations with markets still
        # in db
        df_relations = self.relations.filter(
            id_markt__in=market_ids).to_pandas()
        del df_relations['kk_strom_nullfall']
        del df_relations['kk_strom_planfall']
        df_relations = df_relations.merge(
            df_nullfall, on=['id_siedlungszelle', 'id_markt'], how='left')
        df_relations = df_relations.merge(
            df_planfall, on=['id_siedlungszelle', 'id_markt'], how='left')
        df_relations.fillna(0, inplace=True)
        df_relations.sort_values(by = ['id_markt', 'id_siedlungszelle'],
                                 inplace=True)


        # should be identical, but take both anyway
        sum_null = df_relations.groupby('id_siedlungszelle',
                                 as_index=False)['kk_strom_nullfall'].sum()
        sum_plan = df_relations.groupby('id_siedlungszelle',
                                 as_index=False)['kk_strom_planfall'].sum()
        df_relations = df_relations.merge(sum_null, on=['id_siedlungszelle'],
                            suffixes=('', '_sum'))
        df_relations = df_relations.merge(sum_plan, on=['id_siedlungszelle'],
                            suffixes=('', '_sum'))
        df_relations['kk_bindung_nullfall'] = (df_relations['kk_strom_nullfall'] *
                                        100 / df_relations['kk_strom_nullfall_sum'])
        df_relations['kk_bindung_planfall'] = (df_relations['kk_strom_planfall'] *
                                        100 / df_relations['kk_strom_planfall_sum'])

        # lazy replacing instead of updating, removing old entries this way
        self.log(u'Schreibe Kenngrößen in Datenbank...')
        self.relations.table.truncate()
        self.relations.update_pandas(df_relations)

    def get_markets_in_user_centers(self):
        ''' find markets in user defined centers by spatial joining '''
        centers = self.centers.filter(nutzerdefiniert=1)
        mapping = {}
        for center in centers:
            res = intersect(self.markets, [center], input_fields=['id'],
                            epsg=self.project.settings.EPSG)
            mapping[center.id] = [r['id'] for r in res]
        return mapping

    def update_centers(self):
        '''calculate the sales of the defined centers'''

        df_markets = self.markets.to_pandas().rename(columns={'AGS': 'ags'})

        # Zentralität needs turnovers including new and changed markets
        # copy column for use in Zentralität, as it will be changed in the next step
        df_markets['umsatz_planfall_full'] = df_markets['umsatz_planfall']

        # exclude new markets by setting their turnovers to zero
        new_market_idx = df_markets['id_betriebstyp_nullfall'] == 0
        df_markets.loc[new_market_idx, 'umsatz_planfall'] = 0

        self.centers.filter()
        df_centers = self.centers.to_pandas(
            columns=['fid', 'ags', 'rs', 'ew', 'kk', 'nutzerdefiniert'])

        # ignore turnover changes for existing markets that have been changed
        changed_market_idx = np.logical_and(
            (df_markets['id_betriebstyp_nullfall']
             != df_markets['id_betriebstyp_planfall']),
            df_markets['id_betriebstyp_nullfall'] != 0)
        df_markets.loc[changed_market_idx, 'umsatz_planfall'] = \
            df_markets.loc[changed_market_idx, 'umsatz_nullfall']
        summed = df_markets.groupby('ags').sum()
        del(summed['fid'])
        df_centers_res = df_centers.merge(summed, how='left', on='ags')

        # sum up ags based results to rs
        df_ags_res = df_centers_res[df_centers_res['nutzerdefiniert'] == 0]
        df_ags_agg = df_ags_res.groupby('rs')['ew', 'kk', 'umsatz_planfall',
                                              'umsatz_nullfall',
                                              'umsatz_planfall_full', 'vkfl',
                                              'vkfl_planfall'].sum()
        # -1 indicate the "Verwaltungsgemeinschaften"
        rs_idx = df_centers_res['nutzerdefiniert'] == -1
        for index, row in df_ags_agg.iterrows():
            r_idx = np.logical_and(rs_idx, (df_centers_res['rs'] == index))
            for col in row.keys():
                df_centers_res.loc[r_idx, col] = row[col]

        # get markets in user centers and sum up their values.
        # this spatial joining could be done for ALL centers instead of joining
        # by ags (actually it once was before ags centers were selectable), but
        # for having it done fast, it is only applied for user defined centers
        # now
        user_center_markets = self.get_markets_in_user_centers()
        sum_cols = ['umsatz_planfall', 'umsatz_nullfall',
                    'umsatz_planfall_full', 'vkfl', 'vkfl_planfall']
        for center_id, market_ids in user_center_markets.items():
            mic_idx = df_markets['fid'].isin(market_ids)
            center_idx = df_centers_res['fid'] == center_id
            summed = df_markets.loc[mic_idx, sum_cols].sum().values
            df_centers_res.loc[center_idx, sum_cols] = summed

        df_centers_res['umsatz_differenz'] = (
            100 * (df_centers_res['umsatz_planfall'] /
                   df_centers_res['umsatz_nullfall']) - 100)

        df_centers_res['vkfl_dichte_nullfall'] = (
            df_centers_res['vkfl'] / df_centers_res['ew'])
        df_centers_res['vkfl_dichte_planfall'] = (
            df_centers_res['vkfl_planfall'] / df_centers_res['ew'])
        df_centers_res['vkfl_dichte_differenz'] = (
            df_centers_res['vkfl_dichte_planfall']
            - df_centers_res['vkfl_dichte_nullfall'])

        df_centers_res['zentralitaet_planfall'] = (
            100 * df_centers_res['umsatz_planfall_full'] / df_centers_res['kk'])
        df_centers_res['zentralitaet_nullfall'] = (
            100 * df_centers_res['umsatz_nullfall'] / df_centers_res['kk'])
        df_centers_res['zentralitaet_differenz'] = (
            df_centers_res['zentralitaet_planfall']
            - df_centers_res['zentralitaet_nullfall'])

        df_centers_res.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_centers_res.fillna(0, inplace=True)
        self.centers.filter()
        self.centers.update_pandas(df_centers_res)

    def distances_to_db(self, market_id, destinations, distances, beelines):
        for i, dest in enumerate(destinations):
            self.relations.add(
                id_siedlungszelle=dest.id,
                in_auswahl=True, #dest.in_auswahl,
                id_markt=market_id,
                luftlinie=beelines[i],
                distanz=distances[i],
                geom=dest.geom
            )

