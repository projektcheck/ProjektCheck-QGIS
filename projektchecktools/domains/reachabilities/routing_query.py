# -*- coding: utf-8 -*-
import requests
import json
from pyproj import Proj, transform
import numpy as np
import json
import ogr

from projektchecktools.utils.spatial import Point
from projektchecktools.base.domain import Worker
from projektchecktools.domains.reachabilities.tables import Isochronen
from projektchecktools.domains.definitions.tables import Projektrahmendaten
from settings import settings


class RoutingQuery:
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

    epsg = 4326

    def get_isochrone(self, point, target_epsg, mode, time_sec, walk_speed):
        params = self.isochrone_params.copy()
        params['cutoffSec'] = int(time_sec)
        params['mode'] = mode
        params['walkSpeed'] = walk_speed
        if point.epsg != self.epsg:
            point.transform(self.epsg)
        params['fromPlace'] = '{y},{x}'.format(y = point.y, x = point.x)
        #params['toPlace'] = '53.337871,9.860569'
        #url = ('https://projektcheck.ggr-planung.de/otp/surfaces')
        #r = requests.post(url, params=params, verify=False)
        #sid = r.json()['id']
        #r = requests.get(f'https://projektcheck.ggr-planung.de/otp/surfaces/{sid}')
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
                new_inner_list.append(list(new_list))
            new_coords.append(new_inner_list)
        geom_json['coordinates'] = new_coords
        return geom_json


class Isochrones(Worker):

    categories = [u'Kita', u'Autobahnanschlussstelle', u'Dienstleistungen',
                  u'Ärzte', 'Freizeit', u'Läden',
                  u'Supermarkt/Einkaufszentrum', 'Schule']

    modes = {
        'Auto': ('CAR', 5),
        'Fahrrad': ('BICYCLE', 5),
        'zu Fuß': (u'WALK', 1.33)
    }

    def __init__(self, project, modus='zu Fuß', steps=1,
                 cutoff=10, parent=None):
        super().__init__(parent=parent)
        self.isochronen = Isochronen.features(project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.cutoff_sec = cutoff * 60
        self.n_steps = steps
        self.modus = modus

    def work(self):
        mode, walk_speed = self.modes[self.modus]
        self.log(f'Ermittle die Isochronen für den Modus "{self.modus}"')
        self.isochronen.filter(modus=self.modus)
        self.isochronen.delete()
        self.isochronen.reset()
        table = 'Isochrone'
        centroid = self.project_frame.geom.asPoint()
        epsg = settings.EPSG
        centroid = Point(centroid.x(), centroid.y(), epsg=epsg)
        query = RoutingQuery()
        cutoff_step = self.cutoff_sec / self.n_steps
        for i in reversed(range(self.n_steps)):
            sec = int(cutoff_step * (i + 1))
            self.log(f'...maximale Reisezeit von {sec} Sekunden')
            iso_poly = query.get_isochrone(centroid, epsg,
                                           mode, sec, walk_speed)
            geom = ogr.CreateGeometryFromJson(json.dumps(iso_poly))
            self.isochronen.add(modus=self.modus,
                                sekunden=sec,
                                minuten=round(sec/60, 1),
                                geom=geom)
            self.set_progress(100 * (self.n_steps - i + 1) / self.n_steps)
