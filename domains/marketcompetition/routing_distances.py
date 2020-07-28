# -*- coding: utf-8 -*-
'''
***************************************************************************
    routing_distances.py
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

raster based routing
'''

__author__ = 'Christoph Franke'
__date__ = '14/05/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

import os
import time
import numpy as np
import math
from scipy.ndimage import filters
import tempfile
import processing
from osgeo import gdal
import osr

from projektcheck.utils.spatial import Point, clip_raster
from projektcheck.utils.connection import Request
from projektcheck.settings import settings

requests = Request(synchronous=True)

def dilate_raster(array, kernel_size=3, threshold=120):
    '''
    smooth the borders of areas exceeding the given threshold,
    so that these areas shrink by half the kernel-size along their borders
    '''
    thresh_exceeded = array >= threshold
    ret = np.where(thresh_exceeded, np.nan, array)
    o = kernel_size // 2
    filtered = filters.generic_filter(
        ret, np.nanmedian, (kernel_size, kernel_size), origin=(o, o),
        mode='reflect')
    a = array.copy()
    thresh_exceeded_and_not_nan = thresh_exceeded & ~ np.isnan(filtered)
    #fill_values = filtered[thresh_exceeded]
    a[thresh_exceeded_and_not_nan] = filtered[thresh_exceeded_and_not_nan]
    return a


class RasterManagement:
    '''
    wrapper for a raster file to map coordinates to raster values
    '''
    def __init__(self):
        self.raster_values = self.raster_origin = self.srid = None
        self.cellWidth = self.cellHeight = None
        # map point via id to a raster cell
        self.point_raster_map = {}

    def load(self, raster_file, unreachable=120):
        '''
        load a raster file. unreachable defines time threshold in minutes
        representing unreachable raster cells
        '''
        ds = gdal.OpenEx(raster_file)
        ulx, xres, xskew, uly, yskew, yres = ds.GetGeoTransform()
        try:
            ref = ds.GetSpatialRef()
        # gdal under linux does not seem to have the function above
        except AttributeError:
            ref = osr.SpatialReference(wkt=ds.GetProjection())
        self.srid = int(ref.GetAttrValue('AUTHORITY', 1))
        self.raster_origin = Point(ulx, uly, epsg=self.srid)
        self.cellWidth = xres
        self.cellHeight = abs(yres)

        self.raster_values = dilate_raster(
            np.array(ds.GetRasterBand(1).ReadAsArray()),
            threshold=unreachable
        )

    def register_points(self, points):
        '''
        map given points to raster
        '''
        if self.raster_values is None:
            raise Exception('A raster-file has to be loaded first!')
        for point in points:
            if point.epsg != self.srid:
                point.transform(self.srid)
            mapped_x = int(abs(point.x - self.raster_origin.x) /
                           self.cellWidth)
            mapped_y = int(abs(point.y - self.raster_origin.y) /
                           self.cellHeight)
            self.point_raster_map[point.id] = (mapped_x, mapped_y)

    def get_value(self, point):
        '''
        get value at given point
        '''
        mapped_x, mapped_y = self.point_raster_map[point.id]
        return self.raster_values[mapped_y][mapped_x]


class DistanceRouting:
    '''
    fast routing between an origin and several destinations
    '''
    ROUTER = 'deutschland'
    RASTER_FILE_PATTERN = 'raster_{id}.tif'

    def __init__(self, target_epsg=4326, resolution=300):
        '''
        Parameters
        ----------
        resolution : int, optional
            side length of raster cells in pixels, defaults to 300 pixels
        target_epsg : int, optional
            epsg code of targeted projection, defaults to 4326
        '''
        self.epsg = 4326
        self.resolution = resolution
        self.target_epsg = target_epsg
        self.tmp_folder = tempfile.gettempdir()

    def add_bbox_edge(self, bbox, rel_edge=0.1):
        """
        Change the size of the bbox to avoid rounding errors

        Parameters
        ----------
        bbox : tuple of points
            p1 and p2 define the upper right and the lower left corner of the
            box
        rel_edge : float, optional
            relative factor for enlargement

        Returns
        -------
        tuple
            tuple of points, resized bbox
        """
        p1, p2 = bbox
        bbox_size = abs(p1.x-p2.x)
        edge = bbox_size * rel_edge
        p1_new = Point(p1.x - edge, p1.y - edge, epsg=p1.epsg)
        p2_new = Point(p2.x + edge, p2.y + edge, epsg=p2.epsg)
        ret = (p1_new, p2_new)

        return ret

    def get_distances(self, origin, destinations, bbox=None):
        '''
        estimate the distances between an origin and multiple destinations

        Parameters
        ----------
        origin : Point
        destinations : list of Points
        bbox : tuple of Points, optional
            bounding box to clip the server response (faster)

        Returns
        -------
        tuple
            list of distances of origin to destinations by car and list
            of euclidian distances (both in meters)
        '''
        kmh = 12
        distances = np.ones(len(destinations), dtype=int)
        beelines = np.ones(len(destinations), dtype=int)
        distances.fill(-1)
        dist_raster = self._request_dist_raster(origin, kmh=kmh)
        if dist_raster is None:
            return distances, beelines
        if bbox is not None:
            p1, p2 = self.add_bbox_edge(bbox)
            clipped_raster, raster_epsg = clip_raster(dist_raster, (p1, p2))
            #os.remove(dist_raster)
            dist_raster = clipped_raster
        start = time.time()
        raster = RasterManagement()
        raster.load(dist_raster)
        print('filtering raster {}s'.format(time.time() - start))
        start = time.time()
        raster.register_points(destinations)
        if destinations:
            o = origin.transform(destinations[0].epsg)
        for i, dest in enumerate(destinations):
            try:
                value = raster.get_value(dest)
            # unreachable origins sometimes create a raster too small to
            # allocate the (unreachable) destinations
            except IndexError:
                value = -1
            distance = (value / 60.) * kmh * 1000 if value < 120 else -1
            distances[i] = distance if distance <= 20000 else -1
            # euclidian distance
            beelines[i] = math.sqrt(math.pow(o[0] - dest.x, 2) +
                                    math.pow(o[1] - dest.y, 2))

        #os.remove(dist_raster)
        return distances, beelines

    def _request_dist_raster(self, origin, kmh=30):
        if origin.epsg != self.epsg:
            origin.transform(self.epsg)
        params = {
            'batch': True,
            'routerId': self.ROUTER,
            'fromPlace': f"{origin.y},{origin.x}",
            'mode': 'WALK',
            'maxWalkDistance': 50000,
            'maxPreTransitTime': 1200,
            # the max traveltime will be (cutoffMinutes + 30 min)
            'cutoffMinutes': 70,
            #'searchRadiusM': 1000,
            'walkSpeed': kmh / 3.6,
            'intersectCosts': False,
        }
        start = time.time()
        err_msg = ('Der Server meldet einen Fehler bei der Berechnung. '
                   'Bitte überprüfen Sie die Lage des Punktes '
                   '(innerhalb Deutschlands und max. 1000m '
                   'vom bestehenden Straßennetz entfernt)')
        otp_url = settings.OTP_ROUTER_URL + '/surfaces'
        try:
            r = requests.post(otp_url, params=params)
        except ConnectionError:
            raise Exception(
                'Der Server antwortet nicht. Möglicherweise ist er nicht aktiv '
                'oder überlastet.')
        #except requests.exceptions.HTTPError:
            #raise Exception(err_msg)

        try:
            id = r.json()['id']
        except:
            raise Exception(err_msg)
        url = f'{otp_url}/{id}/raster'

        params = {
            'resolution': self.resolution,
            'crs': f'EPSG:{self.target_epsg}',
        }
        start = time.time()
        r = requests.get(url, params=params)
        print('request get {}s'.format(time.time() - start))
        out_raster = os.path.join(
            self.tmp_folder,
            self.RASTER_FILE_PATTERN.format(id=origin.id))
        if r.status_code == 200:
            with open(out_raster, 'wb') as f:
                f.write(r.raw_data)
        else:
            raise Exception('Das angefragte Distanzraster ist fehlerhaft.')
        return out_raster

