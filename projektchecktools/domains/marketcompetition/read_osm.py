# -*- coding: utf-8 -*-
#
from qgis.core import QgsVectorLayer, QgsField, QgsFeature, QgsGeometry
from qgis.PyQt.Qt import QVariant

from projektchecktools.domains.marketcompetition.markets import (
    Supermarket, ReadMarketsWorker)
from projektchecktools.utils.spatial import (Point, minimal_bounding_poly,
                                             remove_duplicates)
from projektchecktools.domains.marketcompetition.tables import Centers, Markets
from projektchecktools.utils.connection import Request

requests = Request(synchronous=True)


class ReadOSMWorker(ReadMarketsWorker):
    _markets_table = 'Maerkte'
    _max_count = 3000  # max number of markets

    def __init__(self, project, epsg=4326, truncate=False, parent=None):
        super().__init__(project=project, parent=parent)
        self.epsg = epsg
        self.truncate = truncate

    def work(self):
        # get amrkets in minimal bounding polygon (in fact multiple rectangles,
        # as always there is no basic function for minimal bounding polygon)
        communities = Centers.features(project=self.project).filter(
            auswahl__ne=0)
        geometries = [f.geom for f in communities]
        multi_poly = minimal_bounding_poly(geometries)

        self.log('Sende Standortanfrage an Geoserver...')
        reader = OSMShopsReader(epsg=self.epsg)
        if self.truncate:
            osm_markets = Markets.features(
                project=self.project).filter(is_osm=True)
            if len(osm_markets) > 0:
                self.log('Lösche vorhandene OSM-Märkte...')
                osm_markets.delete()
                self.log(f'{len(osm_markets)} OSM-Märkte gelöscht')
            else:
                self.log('Keine OSM-Märkte vorhanden.')
        #if self.par.count.value == 0:
            #return

        markets = []
        for poly in multi_poly.asGeometryCollection():
            # minimal bounding geometry shouldn't contain holes, so it is safe
            # take the first one (all have length = 1)
            polygon = [Point(p.x(), p.y(), epsg=self.epsg)
                       for p in poly.asPolygon()[0]]
            m = reader.get_shops(polygon, count=self._max_count-len(markets))
            markets += m

        self.log(f'{len(markets)} Märkte gefunden')
        self.log('Analysiere gefundene Märkte...')

        markets_in_communities = []
        # convex hulls around communities were passed to geoserver ->
        # some markets are outside
        # ToDo: super inefficient this way, time was pressing :(
        for market in markets:
            for community in communities:
                if community.geom.contains(market.geom):
                    markets_in_communities.append(market)
                    break

        m_layer = QgsVectorLayer(f'Point?crs=EPSG:{self.epsg}', 'markets', 'memory')
        pr = m_layer.dataProvider()
        pr.addAttributes([QgsField('m_id', QVariant.Int)])
        m_layer.updateFields()
        for market in markets:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPointXY(market.geom))
            f.setAttributes([market.id])
            pr.addFeature(f)
        c_layer = QgsVectorLayer(f'Point?crs=EPSG:{self.epsg}', 'layers', 'memory')


        #layer = QgsProject.instance().mapLayersByName('firstLayer')[0]
        #joined_layer = QgsProject.instance().mapLayersByName('secondLayer')[0]

        #parameters = {'INPUT':layer,
                        #'JOIN':joined_layer,
                        #'PREDICATE':[0],
                        #'JOIN_FIELDS':['ID'],
                        #'METHOD':0,
                        #'DISCARD_NONMATCHING':True,
                        #'PREFIX':'new_',
                        #'OUTPUT':'memory:'}

        #processing.runAndLoadResults('qgis:joinattributesbylocation', parameters)

        self.log(f'Schreibe {len(markets)} Märkte in die Datenbank...')
        features = Markets.features(project=self.project)
        self.markets_to_db(markets,
                           truncate=False,  # already truncated osm markets
                           is_buffer=False,
                           is_osm=True)

        features = Markets.features(project=self.project).filter(is_osm=True)
        n = remove_duplicates(features, match_field='id_kette', distance=50)
        self.log('{} Duplikate entfernt...'.format(n))
        self.log('Aktualisiere die AGS der Märkte...')
        # self.set_ags()


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