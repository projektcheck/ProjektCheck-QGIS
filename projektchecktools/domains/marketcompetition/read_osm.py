# -*- coding: utf-8 -*-
#
#from qgis.core import (QgsVectorLayer, QgsField, QgsFeature, QgsGeometry,
                       #QgsApplication)

from projektchecktools.domains.marketcompetition.markets import (
    Supermarket, ReadMarketsWorker)
from projektchecktools.utils.spatial import (Point, minimal_bounding_poly,
                                             remove_duplicates, intersect)
from projektchecktools.domains.marketcompetition.tables import Centers, Markets
from projektchecktools.utils.connection import Request

requests = Request(synchronous=True)


class ReadOSMWorker(ReadMarketsWorker):
    _markets_table = 'Maerkte'
    _max_count = 3000  # max number of markets

    def __init__(self, project, epsg=4326, truncate=False, buffer=0,
                 parent=None):
        super().__init__(project=project, parent=parent)
        self.epsg = epsg
        self.buffer = buffer
        self.truncate = truncate

    def work(self):
        # get amrkets in minimal bounding polygon (in fact multiple rectangles,
        # as always there is no basic function for minimal bounding polygon)
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

        in_com_ids = intersect(markets, communities, input_fields=['id'],
                               epsg=self.epsg)
        in_com_ids = [i['id'] for i in in_com_ids]
        markets_in_com = [m for m in markets if m.id in in_com_ids]

        self.set_progress(50)
        self.log(f'Schreibe {len(markets_in_com)} Märkte in die Datenbank...')
        parsed = self.parse_meta(markets_in_com)

        self.markets_to_db(parsed,
                           truncate=False,  # already truncated osm markets
                           is_buffer=False,
                           is_osm=True)

        self.set_progress(60)
        osm_markets = Markets.features(project=self.project).filter(is_osm=1)
        n = remove_duplicates(osm_markets, match_field='id_kette', distance=50)
        self.log(f'{n} Duplikate entfernt...')
        self.set_progress(80)
        self.log('Ermittle die AGS der Märkte...')
        self.set_ags(osm_markets)


class OSMShopsReader(object):
    geoserver_epsg = 3035

    def __init__(self, epsg=31467):
        self.url = (r'https://geoserver.ggr-planung.de/'
                    r'geoserver/projektcheck/wfs?')
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
        # weird that the geoserver expects a polygon in a different projection
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
            supermarket = Supermarket(id_markt, x, y, epsg=self.epsg,
                                      **properties)
            supermarkets.append(supermarket)
        return supermarkets