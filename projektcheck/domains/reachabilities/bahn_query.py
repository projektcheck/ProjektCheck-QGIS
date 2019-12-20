# -*- coding: utf-8 -*-
import datetime
from time import sleep
import re
import sys
from lxml import html
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta

from projektcheck.utils.spatial import Point
from projektcheck.base.domain import Worker
from projektcheck.base.connection import Request, ConnectionError
from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.domains.reachabilities.tables import (Haltestellen,
                                                        ZentraleOrte,
                                                        ErreichbarkeitenOEPNV)
from projektcheck.utils.spatial import points_within, Point
from settings import settings

requests = Request()


class Stop(Point):
    def __init__(self, x, y, name, distance=0, id=None, epsg=4326):
        super(Stop, self).__init__(x, y, id=id, epsg=epsg)
        self.name = name
        self.distance = distance


class BahnQuery(object):
    reiseauskunft_url = 'http://reiseauskunft.bahn.de/bin/query.exe/dn'
    mobile_url = 'http://mobile.bahn.de/bin/mobil/query.exe/dox'
    timetable_url = u'http://reiseauskunft.bahn.de/bin/bhftafel.exe/dn'

    reiseauskunft_params = {
        'start': 1,
        'S': '',
        'Z': '',
        'date': '',
        'time': ''
    }

    stop_params = {
        'Id': 9627,
        'n': 1,
        'rt': 1,
        'use_realtime_filter': 1,
        'performLocating': 2,
        'tpl': 'stopsnear',
        'look_maxdist': 2000,
        'look_stopclass': 1023,
        'look_x': 0,
        'look_y': 0
    }

    timetable_params = {
        'ld': 96242,
        'country': 'DEU',
        'rt': 1,
        'bt': 'dep',
        'start': 'yes',
        'productsFilter': 1111111111,
        'max': 10000,
        'maxJourneys': 10000,
        'time': '24:00',
        'date': '',
        'evaId': 0,
    }

    date_pattern = '%d.%m.%Y'

    def __init__(self, date=None, timeout=0):
        date = date or datetime.date.today()
        self.date = date.strftime(self.date_pattern)
        self.timeout = timeout

    def _to_db_coord(self, c):
        return ("%.6f" % c).replace('.','')

    def _from_db_coord(self, c):
        return c / 1000000.

    def stops_near(self, point, max_distance=2000, stopclass=1023, n=5000):
        """get closest station to given point (tuple of x,y; epsg: 4326)
        ordered by distance (ascending)
        """
        # set url-parameters
        params = self.stop_params.copy()
        params['look_maxdist'] = max_distance
        params['look_stopclass'] = stopclass
        if point.epsg != 4326:
            raise ValueError('Point has to be in WGS84!')
        params['look_x'] = self._to_db_coord(point.x)
        params['look_y'] = self._to_db_coord(point.y)

        r = requests.get(self.mobile_url, params=params, verify=False)

        root = html.fromstring(r.content)
        rows = root.xpath('//a[@class="uLine"]')

        def parse_href_number(tag, href):
            regex = '{tag}=(\d+)!'.format(tag=tag)
            return re.search(regex, href).group(1)

        stops = []

        for row in rows:
            name = row.text
            if not name:
                continue
            href = row.attrib['href']
            x = int(parse_href_number('X', href))
            y = int(parse_href_number('Y', href))
            id = int(parse_href_number('id', href))
            dist = int(parse_href_number('dist', href))
            stop = Stop(self._from_db_coord(x), self._from_db_coord(y),
                        name, distance=dist,
                        id=id, epsg=4326)
            stops.append(stop)

        # response should be sorted by distances in first place,
        # but do it again because you can
        stops_sorted = sorted(stops, key=lambda x: x.distance)
        if n < len(stops_sorted):
            stops_sorted[:n]

        return stops

    def routing(self, origin_name, destination_name, times, max_retries=1):
        '''
        times - int or str (e.g. 15 or 15:00)
        '''
        params = self.reiseauskunft_params.copy()
        params['date'] = self.date
        params['S'] = origin_name
        params['Z'] = destination_name

        duration = float("inf")
        departure = mode = ''
        changes = 0

        def request_departure_table(time):
            params['time'] = time
            r = requests.get(self.reiseauskunft_url, params=params,
                             verify=False)
            root = html.fromstring(r.content)
            try:
                table = root.get_element_by_id('resultsOverview')
                return table
            except KeyError:
                pass
            return None

        for time in times:
            retries = 0
            while retries <= max_retries:
                table = request_departure_table(time)
                # response contains departures
                if table:
                    break
                # no valid response -> wait and try again
                # (may be caused by too many requests)
                else:
                    sleep(2)
                print('retry')
                retries += 1

            # still no table -> skip
            if not table:
                print('skip')
                continue

            rows = table.xpath('//tr[@class="firstrow"]')

            for row in rows:
                # duration
                content = row.find_class('duration')
                h, m = content[0].text.replace('\n', '').split(':')
                d = int(h) * 60 + int(m)
                # if already found shorter duration -> skip
                if d >= duration:
                    continue
                duration = d

                # departure
                content = [t.text for t in row.find_class('time')]

                matches = re.findall( r'\d{1,2}:\d{1,2}', ' - '.join(content))
                departure = matches[0] if len(matches) > 0 else ''

                # modes
                content = row.find_class('products')
                mode = content[0].text.replace('\n', '')

                # changes
                content = row.find_class('changes')
                changes = int(content[0].text.replace('\n', ''))

            sleep(self.timeout)

        return duration, departure, changes, mode

    def n_departures(self, stop_ids, max_journeys=10000):
        '''stop_ids have to be hafas ids'''
        # set url-parameters
        params = self.timetable_params.copy()
        params['date'] = self.date
        params['maxJourneys'] = max_journeys
        n_departures = []

        for id in stop_ids:
            params['evaId'] = id
            r = requests.get(self.timetable_url, params=params, verify=False)
            root = html.fromstring(r.content)
            rows = root.xpath('//tr')
            journeys = [row for row in rows
                        if row.get('id') and 'journeyRow_' in row.get('id')]
            n_departures.append(len(journeys))
            sleep(self.timeout)

        return n_departures

    def get_timetable_url(self, stop_id):
        params = self.timetable_params.copy()
        params['date'] = self.date
        params['evaId'] = stop_id
        args = ['{}={}'.format(v, k) for v, k in params.items()]
        url = f'{self.timetable_url}?{"&".join(args)}'
        return url


class StopScraper(Worker):

    def __init__(self, project, parent=None):
        super().__init__(parent=parent)
        self.haltestellen = Haltestellen.features(create=True, project=project)
        self.zentrale_orte = ZentraleOrte.features(create=True, project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.query = BahnQuery(date=next_working_day())

    def work(self):
        self.log('Berechne die zentralen Orte und Haltestellen '
                 'in der Umgebung...')
        try:
            self.write_centers_stops()
        except ConnectionError as e:
            self.log('Die Website der Bahn ist nicht erreichbar')
        self.set_progress(50)
        self.log('Ermittle die Anzahl der Abfahrten je Haltestelle...')
        self.update_departures(projectarea_only=True)

    def write_centers_stops(self):
        '''get centers in radius around project centroid, write their closest
        stops and the stops near the project to the db
        '''
        # truncate tables, will be filled in progress
        self.haltestellen.delete()
        self.zentrale_orte.delete()

        centroid = self.project_frame.geom.asPoint()
        df_central = settings.BASEDATA.get_table(
            'Zentrale_Orte', 'Basisdaten_deutschland').to_pandas()
        df_oz = df_central[df_central['OZ'] == 1]
        df_mz = df_central[df_central['OZ'] == 0]

        oz_points = [p.asPoint() for p in df_oz['geom'].values]
        mz_points = [p.asPoint() for p in df_mz['geom'].values]
        oz_points, oz_within = points_within(centroid, oz_points, radius=70000)
        mz_points, mz_within = points_within(centroid, mz_points, radius=30000)
        df_oz_within = df_oz[oz_within]
        df_mz_within = df_mz[mz_within]

        def get_closest_stops(points):
            stops = []
            for point in points:
                t_p = Point(point[0], point[1],
                            epsg=settings.EPSG)
                t_p.transform(4326)
                stops_near = self.query.stops_near(t_p, n=1)
                if len(stops_near) > 0:
                    closest = stops_near[0]
                    stops.append(closest)
            return stops

        oz_stops = get_closest_stops(oz_points)
        mz_stops = get_closest_stops(mz_points)
        if (len(oz_stops) + len(mz_stops)) == 0:
            return

        df_oz_within['id_haltestelle'] = [s.id for s in oz_stops]
        df_mz_within['id_haltestelle'] = [s.id for s in mz_stops]

        df_within = pd.concat([df_oz_within, df_mz_within])
        df_within['name'] = df_within['GEN']
        df_within['id_zentraler_ort'] = df_within['fid']

        del df_within['fid']
        self.zentrale_orte.update_pandas(df_within)

        p_centroid = Point(centroid.x(), centroid.y(),
                           epsg=settings.EPSG)
        p_centroid.transform(4326)
        tfl_stops = self.query.stops_near(p_centroid, n=10)

        self._stops_to_db(oz_stops)
        self._stops_to_db(mz_stops)
        self._stops_to_db(tfl_stops, is_project_stop=1)

    def update_departures(self, projectarea_only=False):
        '''update the db-column 'abfahrten' of the stops with the number
        of departures
        '''
        df_stops = self.haltestellen.filter(
            flaechenzugehoerig=projectarea_only).to_pandas()
        ids = df_stops['id_bahn'].values
        n_departures = self.query.n_departures(ids)
        df_stops['abfahrten'] = n_departures
        self.haltestellen.filter()
        self.haltestellen.update_pandas(df_stops)

    def _stops_to_db(self, stops, is_project_stop=False):
        '''(warning: changes projection of point!)'''
        ids = []
        names = []
        shapes = []
        distances = []

        for stop in stops:
            stop.transform(settings.EPSG)
            self.haltestellen.add(
                geom=stop.geom,
                id_bahn=stop.id,
                name=stop.name,
                flaechenzugehoerig=is_project_stop,
                fussweg=stop.distance,
                abfahrten=0
            )


class BahnRouter(Worker):

    times = range(9, 18)

    def __init__(self, haltestelle, project, recalculate=False, parent=None):
        super().__init__(parent=parent)
        self.origin = haltestelle
        self.recalculate = recalculate
        self.haltestellen = Haltestellen.features(project=project)
        self.zentrale_orte = ZentraleOrte.features(project=project)
        self.erreichbarkeiten = ErreichbarkeitenOEPNV.features(project=project)
        self.query = BahnQuery(date=next_working_day(), timeout=0.5)

    def work(self):
        self.log('Berechne Erreichbarkeit der Zentralen Orte <br> '
                 f'ausgehend von der Haltestelle {self.origin.name}')
        self.routing()

    def routing(self):
        df_centers = self.zentrale_orte.to_pandas()
        df_calculated = self.erreichbarkeiten.to_pandas()
        df_centers['update'] = False
        n_centers = len(df_centers)

        prog_share = 90 / n_centers
        progress = 0

        for i, (index, center) in enumerate(df_centers.iterrows()):
            id_destination = center['id_haltestelle']
            destination = self.haltestellen.get(id_bahn=id_destination)
            self.log(f'  - {destination.name} ({i+1}/{n_centers})')

            progress += prog_share
            if not self.recalculate:
                already_calculated = (
                    (df_calculated['id_origin'] == self.origin.id).values &
                    (df_calculated['id_destination'] == id_destination).values
                ).sum() > 0
                if already_calculated:
                    self.log('bereits berechnet, wird übersprungen')
                    self.set_progress(progress)
                    continue

            try:
                (duration, departure,
                 changes, modes) = self.query.routing(self.origin.name,
                                                      destination.name,
                                                      self.times)
            except ConnectionError:
                self.log('Die Website der Bahn wurde nicht erreicht. '
                         'Bitte überprüfen Sie Ihre Internetverbindung!')
                return
            # just appending results to existing table to write them later
            df_centers.loc[index, 'id_origin'] = self.origin.id
            df_centers.loc[index, 'id_destination'] = id_destination
            df_centers.loc[index, 'ziel'] = destination.name
            df_centers.loc[index, 'abfahrt'] = departure
            if duration != float('inf'):
                df_centers.loc[index, 'dauer'] = str(duration)
            else:
                df_centers.loc[index, 'dauer'] = "???"
            df_centers.loc[index, 'umstiege'] = changes
            df_centers.loc[index, 'verkehrsmittel'] = modes
            df_centers.loc[index, 'update'] = True
            self.set_progress(progress)

        self.log('Schreibe Ergebnisse in die Datenbank...')

        df_update = df_centers[df_centers['update'] == True]
        if len(df_update) > 0:
            self.erreichbarkeiten.update_pandas(
                df_update, pkeys=['id_origin', 'id_destination'])

def next_monday():
    today = date.today()
    nextmonday = today + timedelta(days=-today.weekday(), weeks=1)
    return nextmonday

def next_working_day(min_days_infront=2):
    """
    get the next working day in germany (no holidays, no saturdays, no sundays
    in all federal states)
    reuqires the basetable Feriendichte to hold days infront of today
    (atm data incl. 2017 - 2020)

    Parameters
    ----------
    min_days_infront : int (default: 2)
       returned day will be at least n days infront

    Returns
    -------
    day : datetime.date
       the next day without holidays,
       if day is out of range of basetable: today + min_days_infront
    """

    today = np.datetime64(date.today())

    basedata = settings.BASEDATA

    day = today + np.timedelta64(min_days_infront,'D')
    # get working days (excl. holidays)
    where = ("Wochentag <> 'Samstag' and "
             "Wochentag <> 'Sonntag' and "
             "Anteil_Ferien_Bevoelkerung = 0")
    table = basedata.get_table('Feriendichte', 'Basisdaten_deutschland')
    table.where = where
    df_density = table.to_pandas()
    # can't compare directly because datetime64 has no length
    dates = pd.to_datetime(df_density['Datum'], format='%Y/%m/%d %H:%M:%S.%f')
    df_density['Datum'] = dates.dt.tz_convert(None)
    df_density.sort_values('Datum', inplace=True)
    infront = np.where(df_density['Datum'] >= day)[0]
    if len(infront) > 0:
        # get the first day matching all conditions
        day = df_density.iloc[infront[0]]['Datum']
    return pd.Timestamp(day).date()
