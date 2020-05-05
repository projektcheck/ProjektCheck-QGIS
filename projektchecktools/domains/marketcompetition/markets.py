import re

from projektchecktools.utils.spatial import Point
from projektchecktools.base.domain import Worker
from projektchecktools.utils.connection import Request

requests = Request(synchronous=True)


class Supermarket(Point):
    """A Supermarket"""
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

    def __init__(self, project, epsg=4326, parent=None):
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

    def add_outputs(self):
        group_layer = ("standortkonkurrenz")
        fc = 'Maerkte'
        folder = 'Standortkonkurrenz'
        layer_nullfall = 'Märkte im Bestand'
        layer_changed = 'veränderte Märkte im Bestand'
        layer_planfall = 'geplante Märkte'

        self.output.add_layer(group_layer, layer_nullfall, fc,
                              template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_changed, fc,
                              template_folder=folder, zoom=False)
        self.output.add_layer(group_layer, layer_planfall, fc,
                              template_folder=folder, zoom=False)

        self.output.hide_layer('projektdefinition')

    def markets_to_db(self, supermarkets, tablename='Maerkte', truncate=False,
                      planfall=False, is_buffer=False, start_id=None,
                      is_osm=False):
        """Create the point-features for supermarkets"""
        sr = arcpy.SpatialReference(self.parent_tbx.config.epsg)

        columns = [
            'name',
            'id_betriebstyp_nullfall',
            'id_betriebstyp_planfall',
            'id_kette',
            'betriebstyp_nullfall',
            'betriebstyp_planfall',
            'kette',
            'SHAPE@',
            'id_teilflaeche',
            'id',
            'adresse',
            'is_buffer',
            'is_osm',
            'vkfl',
            'vkfl_planfall',
            'adresse'
        ]
        table = self.folders.get_table(tablename)
        # remove results as well (distances etc.)
        res_table = self.folders.get_table('Beziehungen_Maerkte_Zellen')

        # delete markets of nullfall and ALL results (easiest way)
        if truncate:
            self.parent_tbx.delete_rows_in_table(
                tablename, where='id_betriebstyp_nullfall > 0')
            arcpy.TruncateTable_management(self.folders.get_table(res_table))

        if start_id is None:
            ids = [id for id, in self.parent_tbx.query_table('Maerkte', ['id'])]
            start_id = max(ids) + 1 if ids else 0

        with arcpy.da.InsertCursor(table, columns) as rows:
            for i, market in enumerate(supermarkets):
                if market.name is None:
                    continue
                id_planfall = market.id_betriebstyp
                id_nullfall = 0 if planfall else id_planfall
                bt_nullfall = self.df_bt[self.df_bt['id_betriebstyp']
                                         == id_nullfall].name.values[0]
                bt_planfall = self.df_bt[self.df_bt['id_betriebstyp']
                                         == id_planfall].name.values[0]
                kette = self.df_chains[self.df_chains['id_kette']
                                       == market.id_kette].name.values[0]
                market.create_geom()
                # set sales area, if not set yet (esp. osm markets)
                vkfl = market.vkfl or self.betriebstyp_to_vkfl(market)
                vkfl_nullfall = vkfl if not planfall else 0
                vkfl_planfall = vkfl
                if market.geom:
                    rows.insertRow((
                        market.name,
                        id_nullfall,
                        id_planfall,
                        market.id_kette,
                        bt_nullfall,
                        bt_planfall,
                        kette,
                        market.geom,
                        market.id_teilflaeche,
                        start_id + i,
                        market.adresse,
                        int(is_buffer),
                        int(is_osm),
                        vkfl_nullfall,
                        vkfl_planfall,
                        market.adresse
                    ))

    def set_ags(self):
        """
        Assign community size to supermarkets
        """
        markets = self.folders.get_table('Maerkte')
        ags = get_ags(markets, 'id')
        cursor = arcpy.da.UpdateCursor(markets, ['id', 'AGS'])
        for row in cursor:
            try:
                a = ags[row[0]]
            except:
                continue
            row[1] = a[0]
            cursor.updateRow(row)
        del cursor

    def vkfl_to_betriebstyp(self, markets):
        """
        set types of use (betriebstyp) matching the sales area (vkfl)
        of all given markets
        returns the markets with set types of use
        """
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
                    market.id_betriebstyp = self.df_bt[fit_idx]['id_betriebstyp'].values[0]
        return markets

    def betriebstyp_to_vkfl(self, market):
        """
        return the sales area (vkfl) matching the type of use (betriebstyp)
        of a single market
        """
        # some discounters have (since there is no specific betriebstyp and
        # therefore no hint on possible vkfl for them)
        if market.id_betriebstyp == 7:
            default_vkfl = self.df_chains[
                self.df_chains['id_kette']==market.id_kette]
            if len(default_vkfl) != 0:
                vkfl = default_vkfl['default_vkfl'].values[0]
                return vkfl
        # all other vkfl are assigned via betriebstyp (+ unmatched discounters)
        idx = self.df_bt['id_betriebstyp'] == market.id_betriebstyp
        vkfl = self.df_bt[idx]['default_vkfl'].values[0]
        return vkfl

    def parse_meta(self, markets, field='name'):
        """
        use the name of the markets to parse and assign chain-ids and
        betriebstyps
        """

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

    def delete_area_market(self, id_area):
        '''delete the market corresponding to a planned area and the already
        calculated results for this market'''
        markets = self.folders.get_table('Maerkte')
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
