# -*- coding: utf-8 -*-
'''
***************************************************************************
    markets.py
    ---------------------
    Date                 : May 2019
    Copyright            : (C) 2019 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

base classes for importing markets
'''

__author__ = 'Christoph Franke'
__date__ = '04/05/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

import re
import pandas as pd
from typing import List, Union

from projektcheck.utils.spatial import Point
from projektcheck.base.domain import Worker
from projektcheck.utils.connection import Request
from projektcheck.utils.utils import get_ags
from .tables import Markets, MarketCellRelations

requests = Request(synchronous=True)


class Supermarket(Point):
    '''
    representation of a supermarket, taken from ArcGIS-version to keep the
    interface used in some auxiliary functions in this domain

    ToDo: replace this with the actual Feature
    '''
    def __init__(self, id, x, y, name, kette, betriebstyp='', shop=None,
                 typ=None, vkfl=None, id_betriebstyp=1, epsg=4326,
                 id_teilflaeche=-1, id_kette=0, adresse='', **kwargs):
        super().__init__(x, y, id=id, epsg=epsg)
        self.id_betriebstyp = id_betriebstyp
        self.betriebstyp = betriebstyp
        self.name = name
        self.id_kette = 0
        self.kette = kette
        self.shop = shop
        self.typ = typ
        self.vkfl = vkfl
        self.id_teilflaeche = id_teilflaeche
        self.adresse = adresse

    def __repr__(self):
        return f'{self.kette}, {self.name}'


class ReadMarketsWorker(Worker):
    '''
    abstract worker for parsing, converting and writing markets to the database
    '''
    def __init__(self, project, epsg=4326, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project to add the markets to
        epsg : int, optional
            epsg code of projection of markets, defaults to 4326
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.project = project
        self.epsg = epsg
        basedata = project.basedata
        ws_name = 'Standortkonkurrenz_Supermaerkte'
        self.df_chains = basedata.get_table(
            'Ketten', workspace=ws_name).to_pandas()
        self.df_bt = basedata.get_table(
            'Betriebstypen', workspace=ws_name).to_pandas()
        self.df_bt.fillna(float('inf'), inplace=True)

        self.df_chains_alloc = basedata.get_table(
            'Ketten_Zuordnung', workspace=ws_name).to_pandas()
        self.df_chains_alloc = self.df_chains_alloc.sort_values(
            by='prioritaet', ascending=False)

    def work(self):
        ''''''

    def markets_to_db(self, markets: List[Supermarket], truncate: bool = False,
                      planfall: bool = False, is_osm: bool = False
                      ) -> 'Feature':
        '''
        write markets to the database

        Parameters
        ----------
        truncate : bool, optional
            remove existing status quo markets (keeping planned ones) and
            results, defaults to keep existing markets and results
        planfall : bool, optional
            markets are planned (scenario), defaults to status quo markets
        is_osm : bool, optional
            markets are tagged as retrieved by OSM, defaults to normal markets

        Returns
        -------
        Feature
            the created feature
        '''
        market_feats = Markets.features(project=self.project)
        # delete markets of nullfall ( and ALL results (easiest way)
        if truncate:
            # markets of nullfall (having a "betriebstyp" in nullfall, but not
            # the ones of the planned areas)
            nullfall_markets = market_feats.filter(
                id_betriebstyp_nullfall__gt=0,
                id_teilflaeche__lt=0)
            nullfall_markets.delete()
            MarketCellRelations.features(project=self.project).delete()

        created = []
        for i, market in enumerate(markets):
            if market.name is None or not market.geom:
                continue
            id_planfall = market.id_betriebstyp
            id_nullfall = 0 if planfall else id_planfall
            bt_nullfall = self.df_bt[self.df_bt['id_betriebstyp']
                                     == id_nullfall].name.values[0]
            bt_planfall = self.df_bt[self.df_bt['id_betriebstyp']
                                     == id_planfall].name.values[0]
            kette = self.df_chains[self.df_chains['id_kette']
                                   == market.id_kette].name.values[0]
            # set sales area, if not set yet (esp. osm markets)
            vkfl = market.vkfl or self.betriebstyp_to_vkfl(
                market.id_betriebstyp, market.id_kette)
            vkfl_nullfall = vkfl if not planfall else 0
            vkfl_planfall = vkfl
            feat = market_feats.add(
                name=market.name,
                id_betriebstyp_nullfall=id_nullfall,
                id_betriebstyp_planfall=id_planfall,
                id_kette=market.id_kette,
                betriebstyp_nullfall=bt_nullfall,
                betriebstyp_planfall=bt_planfall,
                kette=kette,
                id_teilflaeche=market.id_teilflaeche,
                is_osm=is_osm,
                vkfl=vkfl_nullfall,
                vkfl_planfall=vkfl_planfall,
                adresse=market.adresse,
                geom=market.geom
            )
            created.append(feat)
        return created

    def set_ags(self, markets: Union[List['Feature']]):
        '''
        assign community size to markets
        '''
        gem = get_ags(markets, self.project.basedata)
        for i, market in enumerate(markets):
            market.AGS = gem[i].AGS
            market.save()

    def vkfl_to_betriebstyp(self, markets: List[Supermarket]
                            ) -> List[Supermarket]:
        '''
        set types of use (betriebstyp) matching the sales area (vkfl)
        of all given markets
        returns the markets with set types of use
        '''
        for market in markets:
            if market.id_kette > 0:
                idx = self.df_chains['id_kette'] == market.id_kette
                is_discounter = self.df_chains[idx]['discounter'].values[0]
            else:
                market.id_kette = 0
                is_discounter = 0
            if is_discounter:
                market.id_betriebstyp = 7
            elif market.vkfl is not None:
                fit_idx = ((self.df_bt['von_m2'] < market.vkfl) &
                           (self.df_bt['bis_m2'] >= market.vkfl))
                if fit_idx.sum() > 0:
                    market.id_betriebstyp = \
                        self.df_bt[fit_idx]['id_betriebstyp'].values[0]
            market.betriebstyp = self.df_bt[
                self.df_bt['id_betriebstyp'] == market.id_betriebstyp
                ].name.values[0]
        return markets

    def betriebstyp_to_vkfl(self, id_betriebstyp: int, id_kette: int
                            ) -> pd.DataFrame:
        '''
        return the sales area (vkfl) matching the type of use (betriebstyp)
        of a single market
        '''
        # some discounters have (since there is no specific betriebstyp and
        # therefore no hint on possible vkfl for them)
        if id_betriebstyp == 7:
            default_vkfl = self.df_chains[
                self.df_chains['id_kette']==id_kette]
            if len(default_vkfl) != 0:
                vkfl = default_vkfl['default_vkfl'].values[0]
                return vkfl
        # all other vkfl are assigned via betriebstyp (+ unmatched discounters)
        idx = self.df_bt['id_betriebstyp'] == id_betriebstyp
        vkfl = self.df_bt[idx]['default_vkfl'].values[0]
        return vkfl

    def parse_meta(self, markets: List[Supermarket], field: str = 'name'
                   ) -> List[Supermarket]:
        '''
        use the name of the markets to parse and assign chain-ids and
        betriebstyps
        '''

        ret_markets = []

        for market in markets:
            # no name -> nothing to parse
            name = getattr(market, field)
            if name is not None:
                try:
                    name = str(name)
                except:
                    pass
            if not name:
                self.log(f'  - Markt mit fehlendem Attribut "{field}" wird '
                         'übersprungen')
                continue
            match_found = False
            for idx, chain_alloc in self.df_chains_alloc.iterrows():
                match_result = re.match(chain_alloc['regex'], name)
                if not match_result:
                    continue
                match_found = True
                id_kette = chain_alloc['id_kette']
                # don't add markets with id -1 (indicates markets that
                # don't qualify as supermarkets or discounters)
                if id_kette >= 0:
                    market.id_betriebstyp = chain_alloc['id_betriebstyp']
                    market.id_kette = id_kette
                    ret_markets.append(market)
                else:
                    self.log(
                        f'  - Markt "{market.name}" ist kein '
                        'Lebensmitteleinzelhandel, wird übersprungen')
                break
            # markets that didn't match (keep defaults)
            if not match_found:
                ret_markets.append(market)
        return ret_markets

    def delete_area_market(self, id_area: int):
        '''
        delete the market corresponding to a planned area and the already
        calculated results for this market
        '''
        where = 'id_teilflaeche={}'.format(id_area)
        rows = self.parent_tbx.query_table(
            'Maerkte', columns=['id'], where=where)
        if not rows:
            return
        # delete all results (there should be only one market per area,
        # but iterate anyway if sth went wrong before)
        for row in rows:
            market_id = row[0]
            self.parent_tbx.delete_rows_in_table(
                'Beziehungen_Maerkte_Zellen',
                where='id_markt = {}'.format(market_id))
        # delete the market
        self.parent_tbx.delete_rows_in_table(
            'Maerkte', where=where)
