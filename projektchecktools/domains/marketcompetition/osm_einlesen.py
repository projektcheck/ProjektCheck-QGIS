# -*- coding: utf-8 -*-
#
import requests
import os
from collections import OrderedDict
import urllib
import re

from projektchecktools.utils.spatial import Point
from settings import settings


class Supermarket(Point):
    """A Supermarket"""
    def __init__(self, id, x, y, name, kette, betriebstyp='', shop=None,
                 typ=None, vkfl=None, id_betriebstyp=1, epsg=4326,
                 id_teilflaeche=-1, id_kette=0, adresse='', **kwargs):
        super(Supermarket, self).__init__(x, y, id=id, epsg=epsg)
        self.id_betriebstyp = id_betriebstyp
        self.betriebstyp = betriebstyp
        self.name = name
        self.id_kette = 0
        self.kette = kette
        self.shop = shop
        self.typ = typ
        self.vkfl = vkfl
        self.geom = None
        self.id_teilflaeche = id_teilflaeche
        self.adresse = adresse

    def __repr__(self):
        return u'{},{}'.format(self.kette, self.name)


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
            arcpy.AddMessage('Fehler bei der Anfrage des Geoservers.')
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
        n_features = len(features)
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
