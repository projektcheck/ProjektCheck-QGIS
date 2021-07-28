# -*- coding: utf-8 -*-
'''
***************************************************************************
    isochrones.py
    ---------------------
    Date                 : October 2019
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

query isochrones from OpenTripPlanner
'''

__author__ = 'Christoph Franke'
__date__ = '29/10/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

import json
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsGeometry, QgsWkbTypes)
import json
from osgeo import ogr

from projektcheck.utils.spatial import Point
from projektcheck.base.domain import Worker
from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.settings import settings
from projektcheck.utils.connection import Request
from .tables import Isochronen

requests = Request(synchronous=True)


class Isochrones(Worker):
    '''
    worker to query and save isochrones with different modes and cutoff times
    '''
    isochrone_url = (f'{settings.OTP_ROUTER_URL}/routers/'
                     f'{settings.OTP_ROUTER_ID}/isochrone')
    # default query parameters
    isochrone_params = {
        'routerId': settings.OTP_ROUTER_ID,
        'algorithm': 'accSampling', # 'algorithm': 'recursiveGrid',
        'maxWalkDistance': 4000,
        'fromPlace': '0, 0',
        'mode': 'WALK',
        'cutoffSec': 600,
        'walkSpeed': 1.33,
        'offRoadDistanceMeters': 500,
        'bikeSpeed': 5.0,
    }

    # pretty names of modes, their OTP tags and speed
    modes = {
        'Auto': ('CAR', 5),
        'Fahrrad': ('BICYCLE', 5),
        'zu Fuß': ('WALK', 1.33)
    }

    def __init__(self, project, modus='zu Fuß', connector=None, steps=1,
                 cutoff=10, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project
        modus : str, optional
            (german) name of the traffic mode ('Auto', 'Fahrrad' or 'zu Fuß'),
            defaults to 'zu Fuß' (walking)
        connector : Feature, optional
            the traffic connector to route from, defaults to the center of the
            project areas
        steps : int, optional
            the number of equal isochrones (equal in time), defaults to one
            isochrone
        cutoff : int, optional
            the maximum cutoff time of the outer isochrone, defaults to ten
            minutes
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.isochronen = Isochronen.features(project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.cutoff_sec = cutoff * 60
        self.n_steps = steps
        self.modus = modus
        self.connector = connector

    def work(self):
        mode, walk_speed = self.modes[self.modus]
        self.log(f'Ermittle die Isochronen für den Modus "{self.modus}"')
        conn_id = self.connector.id if self.connector else -1
        self.isochronen.filter(modus=self.modus, id_connector=conn_id)
        self.isochronen.delete()
        self.isochronen.reset()
        point = self.connector.geom.asPoint() if self.connector \
            else self.project_frame.geom.asPoint()

        epsg = settings.EPSG
        point = Point(point.x(), point.y(), epsg=epsg)
        cutoff_step = self.cutoff_sec / self.n_steps
        for i in reversed(range(self.n_steps)):
            sec = int(cutoff_step * (i + 1))
            self.log(f'...maximale Reisezeit von {sec} Sekunden')
            json_res = self._get_isochrone(point, mode, sec, walk_speed)
            if not json_res:
                continue
            iso_poly = ogr.CreateGeometryFromJson(json.dumps(json_res))
            geom = QgsGeometry.fromWkt(iso_poly.ExportToWkt())
            tr = QgsCoordinateTransform(
                QgsCoordinateReferenceSystem('epsg:4326'),
                QgsCoordinateReferenceSystem(f'epsg:{epsg}'),
                QgsProject.instance()
            )
            geom.transform(tr)
            # the router sometimes returns broken geometries
            if not geom.isGeosValid():
                geom = geom.makeValid()
                # the junk is appended to a collection, discard it
                if geom.wkbType() == QgsWkbTypes.GeometryCollection:
                    geom = geom.asGeometryCollection()[0]
            self.isochronen.add(modus=self.modus,
                                sekunden=sec,
                                minuten=round(sec/60, 1),
                                geom=geom,
                                id_connector=conn_id)
            self.set_progress(100 * (self.n_steps - i + 1) / self.n_steps)

    def _get_isochrone(self, point, mode, time_sec, walk_speed):
        params = self.isochrone_params.copy()
        params['cutoffSec'] = int(time_sec)
        params['mode'] = mode
        params['walkSpeed'] = walk_speed
        if point.epsg != 4326:
            point.transform(4326)
        params['fromPlace'] = '{y},{x}'.format(y = point.y, x = point.x)
        r = requests.get(self.isochrone_url, params=params)
        r.raise_for_status()
        # always returns a collection with a single feature
        geo_json = r.json()['features'][0]['geometry']
        if not geo_json:
            return
        return geo_json