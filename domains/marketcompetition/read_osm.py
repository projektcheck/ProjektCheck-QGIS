# -*- coding: utf-8 -*-
'''
***************************************************************************
    market_templates.py
    ---------------------
    Date                 : May 2020
    Copyright            : (C) 2020 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

request and import markets from OSM data
'''

__author__ = 'Christoph Franke'
__date__ = '04/05/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

from projektcheck.utils.spatial import (Point, minimal_bounding_poly,
                                        remove_duplicates, intersect)
from projektcheck.utils.connection import Request
from projektcheck.settings import settings
from .tables import Centers, Markets
from .markets import Supermarket, ReadMarketsWorker

requests = Request(synchronous=True)


class ReadOSMWorker(ReadMarketsWorker):
    '''
    worker for importing markets from osm into the study area
    '''
    _markets_table = 'Maerkte'
    _max_count = 3000  # max number of markets

    def __init__(self, project, epsg=4326, truncate=False, buffer=0,
                 parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project to add the markets to
        epsg : int, optional
            epsg code of projection of markets, defaults to 4326
        truncate : bool, optional
            remove existing osm markets, defaults to keeping markets
        buffer : int, optional
            buffer around the selected study area to find markets in, defaults
            to no buffer
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(project=project, parent=parent)
        self.epsg = epsg
        self.buffer = buffer
        self.truncate = truncate

    def work(self):
        # get markets in minimal bounding polygon
        communities = Centers.features(project=self.project).filter(
            auswahl__ne=0, nutzerdefiniert=-1)
        geometries = [f.geom for f in communities]
        multi_poly = minimal_bounding_poly(geometries)
        multi_poly = multi_poly.buffer(self.buffer, 1)
        if self.truncate:
            osm_markets = Markets.features(
                project=self.project).filter(is_osm=True)
            n = len(osm_markets)
            if n > 0:
                self.log('Lösche vorhandene OSM-Märkte...')
                osm_markets.delete()
                self.log(f'{n} OSM-Märkte gelöscht')
            else:
                self.log('Keine OSM-Märkte vorhanden.')

        self.log('Sende Standortanfrage an Geoserver...')
        reader = OSMShopsReader(epsg=self.epsg)
        markets = []
        for poly in multi_poly.asGeometryCollection():
            # minimal bounding geometry shouldn't contain holes, so it is safe
            # take the first one (all have length = 1)
            polygon = [Point(p.x(), p.y(), epsg=self.epsg)
                       for p in poly.asPolygon()[0]]
            m = reader.get_shops(polygon, count=self._max_count-len(markets))
            markets += m

        self.set_progress(30)
        self.log(f'{len(markets)} Märkte gefunden')
        self.log('Verschneide gefundene Märkte...')

        communities = Centers.features(project=self.project).filter(
            nutzerdefiniert=-1, auswahl__ne=0)
        in_com_ids = intersect(markets, communities, input_fields=['id'],
                               epsg=self.epsg, buffer=self.buffer)
        in_com_ids = [str(i['id']) for i in in_com_ids]
        markets_in_com = [m for m in markets if str(m.id) in in_com_ids]

        self.set_progress(50)
        self.log(f'Schreibe {len(markets_in_com)} Märkte in die Datenbank...')
        parsed = self.parse_meta(markets_in_com)

        self.markets_to_db(parsed,
                           truncate=False,  # already truncated osm markets
                           is_osm=True)

        self.set_progress(60)
        osm_markets = Markets.features(project=self.project).filter(is_osm=1)
        n = remove_duplicates(osm_markets, match_field='id_kette', distance=50)
        self.log(f'{n} Duplikate entfernt...')
        self.set_progress(80)
        self.log('Ermittle die AGS der Märkte...')
        self.set_ags(osm_markets)


class OSMShopsReader(object):
    '''
    request osm markets from geoserver
    '''
    geoserver_epsg = 3035

    def __init__(self, epsg=31467):
        '''
        Parameters
        ----------
        epsg : int
            epsg code of projection the markets will be in
        '''
        self.url = settings.GEOSERVER_URL + '/wfs?'
        self.wfs_params = dict(service='WFS',
                               request='GetFeature',
                               version='2.0.0',
                               typeNames='projektcheck:supermaerkte',
                               outputFormat='application/json')
        self.epsg = epsg


    def get_shops(self, polygon, count=1000):
        '''
        get shops from osm in the given area

        Parameters
        ----------
        polygon : list
            list of points spanning the area the markets should be in
        count : int, optional
            max. number of returned markets, defaults to 1000

        Returns
        -------
        list
            list of Supermarkets
        '''
        query = 'INTERSECTS(geom,POLYGON(({})))'
        # weird: the geoserver expects a polygon in a different projection
        # (always 3035) than the passed srs
        poly_trans = [p.transform(self.geoserver_epsg) for p in polygon]
        str_poly = ', '.join(('{} {}'.format(pnt[1], pnt[0])
                              for pnt in poly_trans))
        srsname = 'EPSG:{}'.format(self.epsg)
        params = dict(CQL_FILTER=query.format(str_poly),
                      srsname=srsname,
                      count=str(count))
        params.update(self.wfs_params)
        r = requests.get(self.url, params=params)
        if r.status_code != 200:
            raise Exception('Fehler bei der Anfrage des Geoservers.')
        json = r.json()
        return self._decode_json(json)

    def _decode_json(self, json):
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
            supermarket = Supermarket(id_markt, x, y, epsg=self.epsg,
                                      **properties)
            supermarkets.append(supermarket)
        return supermarkets