import requests
import json

from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.domains.reachabilities.tables import Einrichtungen
from projektcheck.base.domain import Worker
from settings import settings

from projektcheck.utils.spatial import Point


class Feature(Point):
    def __init__(self, x, y, name, category, id=None, epsg=4326):
        super(Feature, self).__init__(x, y, id, epsg)
        self.name = name
        self.category = category


class GeoserverQuery(object):
    feature_url = ('https://geoserver.ggr-planung.de/geoserver/projektcheck/wfs')

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

    epsg = 3035


    def get_features(self, point, radius, categories, target_epsg):
        '''return list of Features within given radius around point'''
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

    _param_projectname = 'projectname'
    _workspace = 'FGDB_Erreichbarkeit.gdb'
    cutoff = None

    categories = [u'Kita', u'Autobahnanschlussstelle', u'Dienstleistungen',
                  u'Ärzte', 'Freizeit', u'Läden',
                  u'Supermarkt/Einkaufszentrum', 'Schule']

    def __init__(self, project, radius=1, parent=None):
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
