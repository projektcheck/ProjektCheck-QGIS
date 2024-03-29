# -*- coding: utf-8 -*-
'''
***************************************************************************
    bahn_query.py
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

scrapers for public stops and public transport connections
'''

__author__ = 'Christoph Franke'
__date__ = '29/10/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

import datetime
from time import sleep
import re
from lxml import html
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta

from projektcheck.utils.spatial import Point
from projektcheck.base.domain import Worker
from projektcheck.utils.connection import Request
from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.utils.spatial import points_within, Point
from projektcheck.base.project import ProjectManager
from projektcheck.settings import settings
from .tables import Haltestellen, ZentraleOrte, ErreichbarkeitenOEPNV

requests = Request(synchronous=True)


class Stop(Point):
    '''
    representation of a public stop, taken from ArcGIS-version to keep the
    interface used in some auxiliary functions in this domain

    ToDo: replace this with the actual Feature
    '''
    def __init__(self, x, y, name, distance=0, id=None, epsg=4326):
        super(Stop, self).__init__(x, y, id=id, epsg=epsg)
        self.name = name
        self.distance = distance


class BahnQuery(object):
    '''
    Deutsche-Bahn-scraper for connections, stops and time tables
    '''
    reiseauskunft_url = 'https://reiseauskunft.bahn.de/bin/query.exe/dn'
    mobile_url = 'https://mobile.bahn.de/bin/mobil/query.exe/dox'
    timetable_url = 'https://reiseauskunft.bahn.de/bin/bhftafel.exe/dn'

    # default request parameters for connections
    reiseauskunft_params = {
        'start': 1,
        'S': '',
        'Z': '',
        'date': '',
        'time': ''
    }

    # default request parameters for public stops
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

    # default request parameters for timetables
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
        '''
        Parameters
        ----------
        date : datetime.date, optional
            date to scrape data for, defaults to today
        timeout : int, optional
            pause between requests in seconds to avoid block due to too many
            requests, defaults to no pause
        '''
        date = date or datetime.date.today()
        self.date = date.strftime(self.date_pattern)
        self.timeout = timeout

    def _to_db_coord(self, c):
        return ("%.6f" % c).replace('.','')

    def _from_db_coord(self, c):
        return c / 1000000.

    def stops_near(self, point, max_distance=2000, stopclass=1023, n=5000):
        '''
        get closest station to given point

        Parameters
        ----------
        point : tuple
            x, y values in WGS84 (4326)
        max_distance : int
            maximum distance of stops to given point
        stopclass : int
            id of internal DB stop class
        n : int
            maximum number of stops returned

        Returns
        -------
        list
            stops ordered by distance (ascending)
        '''
        # set url-parameters
        params = self.stop_params.copy()
        params['look_maxdist'] = max_distance
        params['look_stopclass'] = stopclass
        x, y = point
        params['look_x'] = self._to_db_coord(x)
        params['look_y'] = self._to_db_coord(y)

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
            stops = stops_sorted[:n]

        return stops

    def routing(self, origin_name, destination_name, times, max_retries=1):
        '''
        scrape fastest connection by public transport between origin and
        destination

        Parameters
        ----------
        origin_name : str
            address or station name to depart from
        destination_name : str
            address or station name to arrive at
        times : list of int or list of str
            departure times (e.g. [14, 15, 16] or [14:00, 15:00, 16:00])
        max_retries : int
            maximum number of retries per time slot if DB api is returning
            valid results

        Returns
        -------
        tuple
            duration in minutes, departure time as text, number of changes,
            modes as text
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
        '''
        scrape number of departures for stops with given ids (HAFAS)

        Parameters
        ----------
        stop_ids : list
            HAFAS ids of stops
        max_journeys : int, optional
            maximum number of routes per requested time table
        '''
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
        '''
        set up an url to request the stop with given id
        '''
        params = self.timetable_params.copy()
        params['date'] = self.date
        params['evaId'] = stop_id
        args = ['{}={}'.format(v, k) for v, k in params.items()]
        url = f'{self.timetable_url}?{"&".join(args)}'
        return url


class StopScraper(Worker):
    '''
    worker to scrape and write public stops and number of departures per stop
    '''
    def __init__(self, project, date=None, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        date : datetime.date, optional
            date to scrape number of departures for, defaults to next working
            day
        '''
        super().__init__(parent=parent)
        self.project = project
        self.haltestellen = Haltestellen.features(create=True, project=project)
        self.zentrale_orte = ZentraleOrte.features(create=True, project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.query = BahnQuery(date=date or next_working_day())

    def work(self):
        self.log('Berechne die zentralen Orte und Haltestellen '
                 'in der Umgebung...')
        try:
            self.write_centers_stops()
        except ConnectionError as e:
            self.error.emit('Die Website der Bahn ist nicht erreichbar')
        self.set_progress(50)
        self.log('Ermittle die Anzahl der Abfahrten je Haltestelle...')
        self.update_departures(projectarea_only=True)

    def write_centers_stops(self):
        '''
        get centers in radius around project centroid, write their closest
        stops and the stops near the project to the db
        '''
        # truncate tables, will be filled in progress
        self.haltestellen.delete()
        self.zentrale_orte.delete()

        centroid = self.project_frame.geom.asPoint()
        df_central = self.project.basedata.get_table(
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
                stops_near = self.query.stops_near((t_p.x, t_p.y), n=1)
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
        tfl_stops = self.query.stops_near((p_centroid.x, p_centroid.y), n=10)

        self._stops_to_db(oz_stops)
        self._stops_to_db(mz_stops)
        self._stops_to_db(tfl_stops, is_project_stop=1)

    def update_departures(self, projectarea_only=False):
        '''
        update the db-column 'abfahrten' of the stops with the number
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
        for stop in stops:
            geom = stop.transform(settings.EPSG, inplace=False).geom
            self.haltestellen.add(
                geom=geom,
                id_bahn=stop.id,
                name=stop.name,
                flaechenzugehoerig=is_project_stop,
                fussweg=stop.distance,
                abfahrten=0
            )


class BahnRouter(Worker):
    '''
    worker to scrape and write public routes between a public stop and central
    places
    '''

    times = range(9, 18) # time slots to query connections for

    def __init__(self, haltestelle, project, date=None, parent=None):
        '''
        Parameters
        ----------
        haltestelle : Feature
            the stop to depart from
        project : Poject
            the project
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        date : datetime.date, optional
            date to scrape public connections for, defaults to next working
            day
        '''
        super().__init__(parent=parent)
        self.origin = haltestelle
        self.haltestellen = Haltestellen.features(project=project)
        self.zentrale_orte = ZentraleOrte.features(project=project)
        self.erreichbarkeiten = ErreichbarkeitenOEPNV.features(project=project)
        if not date:
            date = next_working_day()
        self.query = BahnQuery(date=date, timeout=0.5)

    def work(self):
        self.log('Berechne Erreichbarkeit der Zentralen Orte <br> '
                 f'ausgehend von der Haltestelle {self.origin.name}')
        self.routing()

    def routing(self):
        '''
        scrape and write best connections between stop and central places
        '''
        df_centers = self.zentrale_orte.to_pandas()
        df_centers['update'] = False
        n_centers = len(df_centers)

        prog_share = 90 / n_centers
        progress = 0

        for i, (index, center) in enumerate(df_centers.iterrows()):
            id_destination = center['id_haltestelle']
            destination = self.haltestellen.get(id_bahn=id_destination,
                                                flaechenzugehoerig=0)
            self.log(f'  - {destination.name} ({i+1}/{n_centers})')

            progress += prog_share

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
    '''
    Returns
    -------
    datetime.date
       the next monday proceeding from today
    '''
    today = date.today()
    nextmonday = today + timedelta(days=-today.weekday(), weeks=1)
    return nextmonday

def next_working_day(min_days_infront=2):
    '''
    get the next working day in germany (no holidays, no saturdays, no sundays
    in all federal states)
    requires the basetable "Feriendichte" to hold days infront of today

    Parameters
    ----------
    min_days_infront : int (default: 2)
       returned day will be at least n days infront

    Returns
    -------
    datetime.date
       the next day without holidays,
       if day is out of range of basetable: today + min_days_infront
    '''

    today = np.datetime64(date.today())

    basedata = ProjectManager().basedata

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
