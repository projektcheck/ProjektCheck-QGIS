import numpy as np
from pyproj import Proj, transform
from qgis.core import (QgsPointXY, QgsGeometry, QgsVectorLayer, QgsField,
                       QgsFeature, QgsPolygon)
from qgis.PyQt.Qt import QVariant
import processing

from projektchecktools.utils.connection import Request

requests = Request(synchronous=True)


class Point(object):
    """A Point object
    taken from ProjektCheck Profi for ArcGIS to be able to use same interface
    """
    def __init__(self, x, y, id=None, epsg=4326):
        self.id = id
        self.x = x
        self.y = y
        self._geom = None
        self.epsg = epsg
        self.proj = Proj(init='epsg:{}'.format(epsg))

    def __repr__(self):
        return '{},{}'.format(self.x, self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    @property
    def geom(self):
        """Create geometry from coordinates"""
        return QgsPointXY(self.x, self.y)

    def transform(self, target_srid):
        target_srid = str(target_srid).lower()
        target_srid = target_srid.replace('epsg:', '')
        # a little weird to replace it and add it again, but i wanted to keep
        # the api of the old ArcGIS Project
        target_srs = Proj(init='epsg:{}'.format(target_srid))
        x, y = transform(self.proj, target_srs, self.x, self.y)
        self.epsg = int(target_srid)
        self.proj = Proj(init='epsg:{}'.format(self.epsg))
        self.x = x
        self.y = y
        return (x, y)

def clip(input_features, overlay_features, output_field='id', epsg=4326):
    '''
    clips features by geometry, only features within the geometries of the
    overlay remain

    Parameters
    ----------
    input_features : list
        list of QgsFeatures with Point geometry to be clipped
    overlay_features : list
        list of QgsFeatures with Polygon geometry
    output_field : string, optional
        name of field in input_features to return, defaults to id
    epsg : int, optional
        epsg code of input and overlay features (should be the same)

    Returns
    -------
    list
        list of values of output_fields of input features within overlay
        geometry
    '''

    def create_layer(features, geom_type, fields=[], name='temp'):
        layer = QgsVectorLayer(f'{geom_type}?crs=EPSG:{epsg}', name, 'memory')
        pr = layer.dataProvider()
        for field in fields:
            pr.addAttributes([QgsField(field, QVariant.String)])
        layer.updateFields()
        for feature in features:
            f = QgsFeature()
            geom = feature.geom
            if isinstance(feature.geom, QgsPointXY):
                geom = QgsGeometry.fromPointXY(feature.geom)
            if isinstance(feature.geom, QgsPolygon):
                geom = QgsGeometry.fromPolygonXY(feature.geom)
            f.setGeometry(geom)
            for field in fields:
                f.setAttributes([getattr(feature, field)])
            pr.addFeature(f)
        return layer

    input_layer = create_layer(input_features, 'Point', fields=[output_field],
                               name='input')
    overlay_layer = create_layer(overlay_features, 'Polygon', name='overlay')

    parameters = {'INPUT': input_layer,
                  'OVERLAY': overlay_layer,
                  'OUTPUT':'memory:'}
    output_layer = processing.run('native:intersection', parameters)['OUTPUT']

    ret = [f.attribute(f.fieldNameIndex(output_field))
           for f in output_layer.getFeatures()]
    return ret

def closest_point(point, points):
    """get the point out of given points that is closest to the given point,
    points have to be passed as tuples of x, y (z optional) coordinates

    Parameters
    ----------
    point : tuple
        x, y (, z) coordinates of point
    points : list of tuples
        x, y (, z) coordinates of points to pick closest one to point from

    Returns
    -------
    index : int
        index of closest point in points
    point : tuple
        x, y of closest point
    """
    distances = _get_distances(point, points)
    closest_idx = distances.argmin()
    return closest_idx, tuple(points[closest_idx])

def points_within(center_point, points, radius):
    """get the points within a radius around a given center_point,
    points have to be passed as tuples of x, y (z optional) coordinates

    Parameters
    ----------
    center_point : tuple or Point
        x, y (, z) coordinates of center-point of circle
    points : list of tuples or list of Points
        x, y (, z) coordinates of points
    radius : int
        radius of circle,
        metric depends on projection of points (e.g. meter if Gauss-Krueger)

    Returns
    -------
    points : list of tuples
        points within radius
    indices : list of bool
        True if point is wihtin radius
    """
    distances = _get_distances(center_point, points)
    is_within = distances <= radius
    return np.array(points)[is_within], is_within

def _get_distances(point, points):
    points = [np.array(p) for p in points]
    diff = np.array(points) - np.array(point)
    distances = np.apply_along_axis(np.linalg.norm, 1, diff)
    return distances

def google_geocode(address, api_key=''):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'sensor': 'false', 'address': address}
    if api_key:
        params['key'] = api_key
    r = requests.get(url, params=params)
    json = r.json()
    results = json['results']
    msg = json['status'] if json.has_key('status') else ''
    if not results:
        if json.has_key('error_message'):
            msg = json['error_message']
        return None, msg
    location = results[0]['geometry']['location']
    return (location['lat'], location['lng']), msg

def minimal_bounding_poly(geometries):
    hulls = []
    for geom in geometries:
        if geom.isMultipart():
            for part in geom.asGeometryCollection():
                hulls.append(part.convexHull())
        else:
            hulls.append(geom.convexHull())

    multi_poly = hulls[0]
    for hull in hulls[1:]:
        multi_poly = multi_poly.combine(hull)
    return multi_poly

def remove_duplicates(features, match_field='', where='', distance=100):
    '''remove point features matched by where clause from the given feature-class
    if other features are within given distance
    match_field - optional, only delete feature, if points within distance have
                  same value in this field
    '''
    add = match_field or 'id'
    all_r = [(f.id, (f.geom.asPoint().x(), f.geom.asPoint().y()),
              getattr(f, add)) for f in features]
    if len(all_r) == 0:
        return 0
    ids, points, mfs = zip(*all_r)
    ids = np.array(ids)
    points = np.array(points)
    mfs = np.array(mfs)
    n_duplicates = 0
    for feature in features:
        point = feature.geom.asPoint()
        p_within, indices = points_within((point.x(), point.y()), points,
                                          distance)
        sub_ids = ids[indices]
        sub_mfs = mfs[indices]
        for p, pid, pmf in zip(p_within, sub_ids, sub_mfs):
            if id == pid:
                continue
            if match_field and getattr(feature, add) != pmf:
                continue
            feature.delete()
            n_duplicates += 1
            break
    return n_duplicates