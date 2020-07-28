# -*- coding: utf-8 -*-
'''
***************************************************************************
    geoserver_query.py
    ---------------------
    Date                 : November 2019
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

geoserver feature queries
'''

__author__ = 'Christoph Franke'
__date__ = '01/11/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.base.domain import Worker
from projektcheck.utils.spatial import Point
from projektcheck.utils.connection import Request
from projektcheck.settings import settings
from .tables import Einrichtungen

requests = Request(synchronous=True)


class Feature(Point):
    '''
    representation of a geoserver feature, taken from ArcGIS-version to keep the
    interface used in some auxiliary functions in this domain

    ToDo: replace this with the actual Feature
    '''
    def __init__(self, x, y, name, category, id=None, epsg=4326):
        super(Feature, self).__init__(x, y, id, epsg)
        self.name = name
        self.category = category


class GeoserverQuery(object):
    '''
    geoserver feature query
    '''
    feature_url = settings.GEOSERVER_URL + '/wfs'

    # default request parameters
    feature_params = {
        'service': 'WFS',
        'request': 'GetFeature',
        'version': '2.0.0',
        'typeNames': 'projektcheck:projektcheck_deutschland',
        'CQL_FILTER': '',
        'count': 10000,
        'outputFormat': 'application/json',
        'srsname': 'EPSG:4326'
    }

    epsg = 3035 # default geoserver projection

    def get_features(self, point, radius, categories, target_epsg):
        '''
        get features within given radius around point

        Parameters
        ----------
        point : Point
            center of area to get features in
        radius : int
            radius spanning area around center point to get features in
        categories : list
            list of categories (strings) of the features, corresponds to the
            tags the features have in the geoserver db
        target_epsg : int
            epsg codes of the returned features

        Returns
        -------
        list
             list of Features
        '''
        if point.epsg != self.epsg:
            point.transform(self.epsg)
        params = self.feature_params.copy()
        params['srsname'] = 'EPSG:{}'.format(target_epsg)
        categories = [u"'{}'".format(c) for c in categories]
        cql_filter = (u'projektcheck_category IN ({cat}) '
                      u'AND DWithin(geom,POINT({y} {x}), {radius}, meters)'
                      .format(cat=u','.join(categories),
                              x=point.x, y=point.y,
                              radius=radius))
        params['CQL_FILTER'] = cql_filter
        r = requests.get(self.feature_url, params=params, verify=False)
        r.raise_for_status()
        feat_dicts = r.json()['features']
        features = []
        for feat in feat_dicts:
            geometry = feat['geometry']
            coords = geometry['coordinates']
            if geometry['type'] == 'Point':
                x, y = coords
            else:
                x, y = coords[0]
            category = feat['properties']['projektcheck_category']
            name = feat['properties']['name'] or ''
            feature = Feature(x, y, name[:99], category, epsg=target_epsg)
            features.append(feature)
        return features


class EinrichtungenQuery(Worker):
    '''
    worker to query locations of interest
    '''

    # feature tags
    categories = [u'Kita', u'Autobahnanschlussstelle', u'Dienstleistungen',
                  u'Ärzte', 'Freizeit', u'Läden',
                  u'Supermarkt/Einkaufszentrum', 'Schule']

    def __init__(self, project, radius=1, parent=None):
        '''
        Parameters
        ----------
        project : Project
            the project
        radius : int, optional
            the radius in km around the project areas to query locations in
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.einrichtungen = Einrichtungen.features(project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.radius = radius

    def work(self):
        self.einrichtungen.delete()
        query = GeoserverQuery()
        radius = self.radius * 1000
        centroid = self.project_frame.geom.asPoint()
        epsg = settings.EPSG
        centroid = Point(centroid.x(), centroid.y(), epsg=epsg)
        self.log('Frage Geoserver an...')
        features = query.get_features(centroid, radius,
                                      self.categories, epsg)
        self.log(f'Schreibe {len(features)} Einrichtungen in die Datenbank...')

        for feat in features:
            self.einrichtungen.add(
                name=feat.name,
                projektcheck_category=feat.category,
                geom=feat.geom
            )
