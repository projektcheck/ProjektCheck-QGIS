import json
from qgis.core import (QgsProject, QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsGeometry, QgsWkbTypes)
import json
import ogr

from projektcheck.utils.spatial import Point
from projektcheck.base.domain import Worker
from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.settings import settings
from projektcheck.utils.connection import Request
from .tables import Isochronen

requests = Request(synchronous=True)


class Isochrones(Worker):
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
        cutoff_step = self.cutoff_sec / self.n_steps
        for i in reversed(range(self.n_steps)):
            sec = int(cutoff_step * (i + 1))
            self.log(f'...maximale Reisezeit von {sec} Sekunden')
            json_res = self.get_isochrone(point, mode, sec, walk_speed)
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

    def get_isochrone(self, point, mode, time_sec, walk_speed):
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