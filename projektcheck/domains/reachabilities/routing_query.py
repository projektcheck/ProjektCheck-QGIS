# -*- coding: utf-8 -*-
import requests
import json
import arcpy
from pyproj import Proj, transform
import numpy as np


class RoutingQuery(object):
    isochrone_url = ('https://projektcheck.ggr-planung.de'
                     '/otp/routers/deutschland/isochrone')
    isochrone_params = {
        'routerId': 'deutschland',
        'algorithm': 'accSampling',
        'maxWalkDistance': 4000,
        'fromPlace': '0, 0',
        'mode': 'WALK',
        'cutoffSec': 600,
        'walkSpeed': 1.33,
        'offRoadDistanceMeters': 500,
        'bikeSpeed': 5.0,
    }

    def __init__(self):
        self.epsg = 4326

    def get_isochrone(self, point, target_epsg, mode, time_sec, walk_speed):
        params = self.isochrone_params.copy()
        params['cutoffSec'] = time_sec
        params['mode'] = mode
        params['walkSpeed'] = walk_speed
        if point.epsg != self.epsg:
            point.transform(self.epsg)
        params['fromPlace'] = '{y},{x}'.format(y = point.y, x = point.x)
        r = requests.get(self.isochrone_url, params=params, verify=False)
        r.raise_for_status()
        geojson = r.json()
        geom_json = geojson['features'][0]['geometry']
        coords = geom_json['coordinates']
        new_coords = []
        p1 = Proj(init='epsg:{}'.format(self.epsg))
        p2 = Proj(init='epsg:{}'.format(target_epsg))
        for a in coords:
            new_inner_list = []
            for b in a:
                arr = np.asarray(b)
                new_arr = transform(p1, p2, arr[:, 0], arr[:, 1])
                new_list = np.array(zip(*new_arr)).tolist()
                new_inner_list.append(new_list)
            new_coords.append(new_inner_list)
        geom_json['coordinates'] = new_coords
        iso_poly = arcpy.AsShape(geom_json)

        #if iso_poly.partCount == 0:
            #return None
        #b = arcpy.DefineProjection_management(iso_poly, arcpy.SpatialReference(4326))
        #epsg = self.epsg
        #parts = []
        #for part in iso_poly:
            #points = []
            #for point in part:
                #p = arcpy.PointGeometry(point,
                                        #arcpy.SpatialReference(self.epsg))
                #points.append(
                    #p.projectAs(arcpy.SpatialReference(31467)).firstPoint)
            #parts.append(arcpy.Array(points))
        #poly_points = arcpy.Array(parts)
        #polygon = arcpy.Polygon(poly_points)
        return iso_poly
