import numpy as np
from pyproj import Proj, transform
from qgis.core import QgsPointXY

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


class Point(object):
    """A Point object
    taken from ProjektCheck ArcGIS to be able to use same interface
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
