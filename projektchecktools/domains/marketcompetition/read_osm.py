# -*- coding: utf-8 -*-
#
import requests
import os
from collections import OrderedDict
import urllib
import re

from projektchecktools.domains.marketcompetition.markets import (
    Supermarket, ReadMarketsWorker)
from projektchecktools.utils.spatial import Point, minimal_bounding_poly
from projektchecktools.domains.marketcompetition.tables import Centers, Markets


class ReadOSMWorker(ReadMarketsWorker):
    _markets_table = 'Maerkte'
    _max_count = 3000  # max number of markets

    def work(self):
        # get amrkets in minimal bounding polygon (in fact multiple rectangles,
        # as always there is no basic function for minimal bounding polygon)
        communities = Centers.features(project=self.project).filter(
            auswahl__ne=0)
        geometries = [f.geom for f in communities]
        multi_poly = minimal_bounding_poly(geometries)

        multi_poly = [[Point(p.X, p.Y, epsg=epsg) for p in poly if p]
                      for poly in multi_poly]

        self.log('Sende Standortanfrage an Geoserver...')
        reader = OSMShopsReader(epsg=self.epsg)
        if self.truncate:
            osm_markets = Centers.features(project=self.project).filter(auswahl__ne=0)
            if len(ids) > 0:
                self.log('Lösche vorhandene OSM-Märkte...')

                self.log(f'{n} OSM-Märkte gelöscht')
            else:
                self.log('Keine OSM-Märkte vorhanden.')
        #if self.par.count.value == 0:
            #return

        markets = []
        for poly in multi_poly:
            m = reader.get_shops(poly, count=self._max_count-len(markets))
            markets += m
        self.log('{} Märkte gefunden'.format(len(markets)))
        self.log('Analysiere gefundene Märkte...'
                         .format(len(markets)))

        markets = self.parse_meta(markets)
        self.log('Schreibe {} Märkte in die Datenbank...'
                         .format(len(markets)))

        markets_tmp = self.folders.get_table('markets_tmp', check=False)
        auswahl_tmp = self.folders.get_table('auswahl_tmp', check=False)
        clipped_tmp = self.folders.get_table('clipped_tmp', check=False)
        def del_tmp():
            for table in [markets_tmp, clipped_tmp, auswahl_tmp]:
                arcpy.Delete_management(table)
        del_tmp()

        markets_table = self.folders.get_table('Maerkte', check=False)
        ids = [id for id, in self.parent_tbx.query_table(markets_table, ['id'])]
        start_id = max(ids) + 1 if ids else 0
        # write markets to temporary table and clip it with selected communities
        arcpy.CreateFeatureclass_management(
            os.path.split(markets_tmp)[0], os.path.split(markets_tmp)[1],
            template=markets_table
        )
        self.markets_to_db(markets,
                           tablename=os.path.split(markets_tmp)[1],
                           truncate=False,  # already truncated osm markets
                           is_buffer=False,
                           is_osm=True,
                           start_id=start_id)

        arcpy.FeatureClassToFeatureClass_conversion(
            communities, *os.path.split(auswahl_tmp),
            where_clause='Auswahl<>0')
        arcpy.Clip_analysis(markets_tmp, auswahl_tmp, clipped_tmp)

        arcpy.Append_management(clipped_tmp, markets_table)
        del_tmp()
        self.log('Entferne Duplikate...')
        n = remove_duplicates(self.folders.get_table(self._markets_table),
                              'id', match_field='id_kette',
                              where='is_osm=1', distance=50)
        self.log('{} Duplikate entfernt...'.format(n))
        self.log('Aktualisiere die AGS der Märkte...')
        self.set_ags()


class OSMShopsReader(object):
    def __init__(self, epsg=31467):
        self.geoserver_epsg = 3035
        self.url = r'https://geoserver.ggr-planung.de/geoserver/projektcheck/wfs?'
        self.wfs_params = dict(service='WFS',
                               request='GetFeature',
                               version='2.0.0',
                               typeNames='projektcheck:supermaerkte',
                               outputFormat='application/json')
        self.epsg = epsg


    def get_shops(self, polygon, count=1000):
        """
        get shops from osm

        Parameters
        ----------
        source : Point
        distance : float
            the distance in meters

        Returns
        -------
        json
        """
        query = 'INTERSECTS(geom,POLYGON(({})))'
        poly_trans = [p.transform(self.geoserver_epsg) for p in polygon]
        str_poly = ', '.join(('{} {}'.format(pnt[1], pnt[0])
                              for pnt in poly_trans))
        srsname = 'EPSG:{}'.format(self.epsg)
        params = dict(CQL_FILTER=query.format(str_poly),
                      srsname=srsname,
                      count=str(count))
        params.update(self.wfs_params)
        new_params = []
        for (k, v) in params.items():
            param = '='.join([urllib.quote(k), urllib.quote(v)])
            new_params.append(param)
        param_str = '&'.join(new_params)
        r = requests.get(self.url, params=param_str)
        try:
            json = r.json()
        except ValueError:
            self.log('Fehler bei der Anfrage des Geoservers.')
            return []
        return self._decode_json(json)

    def _decode_json(self, json):
        """
        Parse the geometry from a json

        Parameters
        ----------
        json : json-instance

        route_id : int

        source_id : int, optional(default=0)

        Returns
        -------
        supermarkets : list
            a list with all supermarkets found
        """
        try:
            features = json['features']
        except KeyError:
            return
        supermarkets = []
        id_markt = 0
        for feature in features:
            id_markt += 1
            x, y = feature['geometry']['coordinates']
            properties = feature['properties']
            supermarket = Supermarket(id_markt, x, y, **properties)
            supermarkets.append(supermarket)
        return supermarkets

    def truncate(self, fc):
        """
        Truncate the table

        Parameters
        ----------
        fc : str
            the table to truncate
        """
        arcpy.TruncateTable_management(in_table=fc)



if __name__ == '__main__':
    o = OSMShopsReader()
    source = Point(54, 10, epsg=4326)
    #source.transform(3035)
    supermarkets = o.get_shops()
    o.create_supermarket_features(supermarkets)
