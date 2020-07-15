import numpy as np
from qgis.core import (QgsPointXY, QgsGeometry, QgsVectorLayer, QgsField,
                       QgsFeature, QgsPolygon, QgsCoordinateTransform,
                       QgsProject, QgsCoordinateReferenceSystem, QgsPoint,
                       QgsFeatureIterator)
from qgis.PyQt.Qt import QVariant
import gdal, osr
from typing import Union, Tuple, List
import os
import tempfile
import processing

from projektcheck.base.database import Table, Feature, FeatureCollection
from .connection import Request

requests = Request(synchronous=True)


class Point(object):
    '''
    A Point object with same interface as required in code taken from
    ProjektCheck Profi for ArcGIS (doing some weird inplace transformations)

    ToDo: replace this with QGIS geometries in code originating from
    ArcGIS-version entirely
    '''
    def __init__(self, x: float, y: float, id: int = None, epsg: int = 4326):
        '''
        Parameters
        ----------
        x : float
            x coordinate
        y : float
            y coordinate
        id : int, optional
            unique identifier, defaults to no id
        epsg : int, optional
            epsg code of projection coordinates are in, defaults to 4326
        '''
        self.id = id
        self.x = x
        self.y = y
        self._geom = None
        self.epsg = epsg

    def __repr__(self):
        return '{},{}'.format(self.x, self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    @property
    def geom(self) -> QgsPointXY:
        '''
        coordinates as QGIS-geometry
        '''
        return QgsPointXY(self.x, self.y)

    def transform(self, target_srid: Union[str, int], inplace: bool = True
                  ) -> 'Point':
        '''
        transform point into different projection

        Parameters
        ----------
        target_srid : str or int
            epsg code to transform to
        inplace : bool, optional
            transform x and y in place if True, return new Point if False and
            keep x and y of this as is, returns to inplace transformation

        Returns
        ----------
        Point
            transformed point if inplace, else None
        '''
        # a little weird to replace it and add it again, but i wanted to keep
        # the api of the old ArcGIS Project
        if isinstance(target_srid, str):
            target_srid = target_srid.replace('epsg:', '')
            target_srid = int(target_srid)

        tr = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(self.epsg),
            QgsCoordinateReferenceSystem(f'epsg:{target_srid}'),
            QgsProject.instance()
        )
        pnt = QgsPoint(self.x, self.y)
        pnt.transform(tr)
        x, y = pnt.x(), pnt.y()
        if inplace:
            self.epsg = target_srid
            self.x = x
            self.y = y
            return (x, y)
        else:
            return Point(x, y, id=self.id, epsg=target_srid)

def clip_raster(raster_file: str, bbox: Tuple[Point, Point]) -> Tuple[str, int]:
    '''
    clip a raster file with given bbox

    Parameters
    ----------
    raster_file : str
        full path to raster file
    bbox : tuple
        upper left and lower right Points

    Returns
    ----------
    tuple
        path to clipped output raster file and epsg code of its projection
    '''
    ds = gdal.OpenEx(raster_file)
    try:
        ref = ds.GetSpatialRef()
    # gdal under linux does not seem to have the function above
    except AttributeError:
        ref = osr.SpatialReference(wkt=ds.GetProjection())
    raster_epsg = ref.GetAttrValue('AUTHORITY',1)
    p1, p2 = bbox
    p1 = p1.transform(raster_epsg, inplace=False)
    p2 = p2.transform(raster_epsg, inplace=False)
    suffix = os.path.splitext(raster_file)[1]
    clipped_raster = tempfile.NamedTemporaryFile(suffix=suffix).name
    clipped = gdal.Translate(clipped_raster, ds,
                             projWin = [p1.x, p2.y, p2.x, p1.y])
    clipped = ds = None
    return clipped_raster, int(raster_epsg)

def get_bbox(table: Table) -> Tuple[Point, Point]:
    '''
    get the minimal bounding box covering all features in table

    Parameters
    ----------
    table : Table
        table with features to be in bounding box

    Returns
    ----------
    tuple
        upper left and lower right Points spanning the bounding box
    '''
    layer = QgsVectorLayer(f'{table.workspace.path}|layername={table.name}')
    layer.dataProvider().updateExtents()
    ex = layer.extent()
    epsg = layer.crs().postgisSrid()
    bbox = (Point(ex.xMinimum(), ex.yMinimum(), epsg=epsg),
            Point(ex.xMaximum(), ex.yMaximum(), epsg=epsg))
    return bbox

def create_layer(features: Union[List[QgsFeature], QgsFeatureIterator],
                 geom_type: str, fields: List[str] = [], name: str = 'temp',
                 epsg: int = 4326, target_epsg: int = None,
                 buffer: float = None) -> QgsVectorLayer:
    '''
    create a vector layer containing given features

    Parameters
    ----------
    features : QgsFeature or QgsFeatureIterator
        features to put into new layer
    geom_type : str
        type of geometry e.g. Point, Polygon
    fields : list, optional
        field names the new layer contains, should match the fields of the
        input features, defaults to no fields
    name : str, optional
        name of the layer, defaults to 'temp'
    epsg : int, optional
        epsg code of projection of the geometries of the input features,
        defaults to 4326
    target_epsg : int, optional
        epsg code of projection of the new layer, defaults to input epsg
        (see parameter 'epsg')
    buffer : float, optional
        buffer around the geometries of the features, metric depends on
        projection of input features (e.g. meter if Gauss-Krueger),
        defaults to no buffer
    '''
    layer = QgsVectorLayer(f'{geom_type}?crs=EPSG:{target_epsg or epsg}',
                           name, 'memory')
    pr = layer.dataProvider()
    for field in fields:
        pr.addAttributes([QgsField(field, QVariant.String)])
    layer.updateFields()
    if target_epsg:
        tr = QgsCoordinateTransform(
            QgsCoordinateReferenceSystem(epsg), layer.crs(),
            QgsProject.instance()
        )
    for feature in features:
        f = QgsFeature()
        geom = feature.geom
        if buffer:
            geom = geom.buffer(buffer, 10)
        if target_epsg:
            geom.transform(tr)
        if isinstance(feature.geom, QgsPointXY):
            geom = QgsGeometry.fromPointXY(feature.geom)
        if isinstance(feature.geom, QgsPolygon):
            geom = QgsGeometry.fromPolygonXY(feature.geom)
        f.setGeometry(geom)
        for field in fields:
            f.setAttributes([getattr(feature, field)])
        pr.addFeature(f)
    return layer

def intersect(input_features: Union[List[QgsFeature], QgsFeatureIterator],
              overlay: Union[QgsVectorLayer,
                             Union[List[QgsFeature], QgsFeatureIterator]],
              input_fields=['id'], output_fields=[], epsg: int = 4326,
              buffer: float = None) -> dict:
    '''
    clips features by geometry, only features within the geometries of the
    overlay remain

    Parameters
    ----------
    input_features : list
        list of QgsFeatures with Point geometry to be clipped
    overlay_features : list or layer
        list of QgsFeatures with Polygon geometry or layer with Polygon geometry
    input_fields : list, optional
        list of names of fields in input_features to return, defaults to [id]
    output_fields : list, optional
        list of names of fields of matched features in overlay_features
        (resp. overlay layer) to return, empty by default
    epsg : int, optional
        epsg code of input and overlay features (should be the same)
    buffer : float, optional
        buffer around the geometries of the overlay features, metric depends on
        projection of overlay features (e.g. meter if Gauss-Krueger),
        defaults to no buffer

    Returns
    -------
    dict
        dict with values of input features within overlay geometry, contains
        values of both given input and output fields
    '''


    input_layer = create_layer(input_features, 'Point', fields=input_fields,
                               name='input', epsg=epsg)
    if not isinstance(overlay, QgsVectorLayer):
        overlay = create_layer(overlay, 'Polygon',
                               name='overlay', fields=output_fields,
                               epsg=epsg, buffer=buffer)

    parameters = {'INPUT': input_layer,
                  'OVERLAY': overlay,
                  'OUTPUT':'memory:'}
    output_layer = processing.run('native:intersection', parameters)['OUTPUT']

    ret_fields = input_fields + output_fields
    ret = [{i: f.attribute(f.fieldNameIndex(i)) for i in ret_fields}
           for f in output_layer.getFeatures()]
    return ret

def closest_point(point: Tuple[float, float], points: List[Tuple[float, float]]
                  ) -> Tuple[int, Tuple[float, float]]:
    '''
    get the point out of given points that is closest to the given point,
    points have to be passed as tuples of x, y (z optional) coordinates

    Parameters
    ----------
    point : tuple
        x, y (, z) coordinates of point
    points : list of tuples
        x, y (, z) coordinates of points to pick closest one to point from

    Returns
    -------
    point : tuple
        index of closest point in points and x, y coordinates of closest point
    '''
    distances = _get_distances(point, points)
    closest_idx = distances.argmin()
    return closest_idx, tuple(points[closest_idx])

def points_within(center_point: Union[tuple, Point],
                  points: Union[List[tuple], List[Point]], radius: float
                  ) -> Tuple[np.ndarray, np.ndarray]:
    '''
    get the points within a radius around a given center_point,
    points have to be passed as tuples of x, y (z optional) coordinates

    Parameters
    ----------
    center_point : tuple or Point
        x, y (, z) coordinates of center-point of circle
    points : list of tuples or list of Points
        x, y (, z) coordinates of points
    radius : float
        radius of circle,
        metric depends on projection of points (e.g. meter if Gauss-Krueger)

    Returns
    -------
    points : list of tuples
        array of x, y coordinates of points within radius and array of booleans
        indicating if coordinates are within given radius
    '''
    distances = _get_distances(center_point, points)
    is_within = distances <= radius
    return np.array(points)[is_within], is_within

def _get_distances(point: Union[tuple, Point],
                   points: Union[List[tuple], List[Point]]) -> np.ndarray:
    '''
    get distances between point and each point in list of points
    '''
    points = [np.array(p) for p in points]
    diff = np.array(points) - np.array(point)
    distances = np.apply_along_axis(np.linalg.norm, 1, diff)
    return distances

def nominatim_geocode(address: str = '', **kwargs
                      ) -> Tuple[Tuple[str, str], str]:
    '''
    geocode address with Nominatim API (nominatim.openstreetmap.org)

    Parameters
    ----------
    address : str, optional
        query string containing whole address (unordered),
        defaults to no address
    **kwargs
        nominatim-specific query parameters:
        street (incl. number), city, postalcode, country, county, state

    Returns
    -------
    tuple
        coordinates (latitude, longitude) and message,
        coordinates are None if geocoding was not succesful
    '''
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'format': 'json'}
    if address:
        params['q'] = address
    for k, v in kwargs.items():
        if v:
            params[k] = v
    r = requests.get(url, params=params)
    results = r.json()
    if not results:
        return None, 'nicht gefunden'
    location = (results[0]['lat'], results[0]['lon'])
    return location, 'gefunden'

def google_geocode(address, api_key=''):
    '''
    geocode address with Google Geocoding API (nominatim.openstreetmap.org)

    Parameters
    ----------
    address : str
        query string containing whole address (unordered)

    Returns
    -------
    tuple
        coordinates (latitude, longitude) and message,
        coordinates are None if geocoding was not succesful
    '''
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'sensor': 'false', 'address': address}
    if api_key:
        params['key'] = api_key
    r = requests.get(url, params=params)
    json = r.json()
    results = json['results']
    msg = json.get('status', '')
    if not results:
        if 'error_message' in json:
            msg = json['error_message']
        return None, msg
    location = results[0]['geometry']['location']
    return (location['lat'], location['lng']), msg

def minimal_bounding_poly(geometries: List[QgsGeometry]) -> QgsGeometry:
    '''
    find minimal bounding polygon covering all given geometries

    Parameters
    ----------
    geometries : list
        list of geometries

    Returns
    -------
    QgsGeometry
        minimal bounding polygon
    '''
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

def remove_duplicates(features: Union[List[Feature], FeatureCollection],
                      match_field: str = '', distance: float = 100) -> int:
    '''
    remove point features from database if other features are within given distance

    Parameters
    ----------
    features : list or QgsFeatureIterator
        features to remove duplicates from
    distance : float, optional
        only delete duplicate feature if it is within this range,
        metric depends on projection of features, defaults to 100
    match_field : str, optional
        only delete features in range if those have same value in this field,
        defaults to delete all in range

    Returns
    -------
    int
        number of removed duplicates
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
            if feature.id == pid:
                continue
            if match_field and getattr(feature, add) != pmf:
                continue
            feature.delete()
            n_duplicates += 1
            break
    return n_duplicates