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
from projektchecktools.utils.connection import Request

requests = Request(synchronous=True)


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

    def get_isochrone(self, point, mode, time_sec, walk_speed,
                      target_epsg=None):
        params = self.isochrone_params.copy()
        params['cutoffSec'] = int(time_sec)
        params['mode'] = mode
        params['walkSpeed'] = walk_speed
        if point.epsg != self.epsg:
            point.transform(self.epsg)
        params['fromPlace'] = '{y},{x}'.format(y = point.y, x = point.x)
        r = requests.get(self.isochrone_url, params=params)
        r.raise_for_status()
        geojson = r.json()
        geom_json = geojson['features'][0]['geometry']
        if geom_json and target_epsg:
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

    def __init__(self, project, modus='zu Fuß', connector=None, steps=1,
                 cutoff=10, parent=None):
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
        query = RoutingQuery()
        cutoff_step = self.cutoff_sec / self.n_steps
        for i in reversed(range(self.n_steps)):
            sec = int(cutoff_step * (i + 1))
            self.log(f'...maximale Reisezeit von {sec} Sekunden')
            iso_poly = query.get_isochrone(point, mode, sec, walk_speed,
                                           target_epsg=epsg)
            if not iso_poly:
                continue
            geom = ogr.CreateGeometryFromJson(json.dumps(iso_poly))
            self.isochronen.add(modus=self.modus,
                                sekunden=sec,
                                minuten=round(sec/60, 1),
                                geom=geom,
                                id_connector=conn_id)
            self.set_progress(100 * (self.n_steps - i + 1) / self.n_steps)
