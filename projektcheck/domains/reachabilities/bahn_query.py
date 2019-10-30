# -*- coding: utf-8 -*-
import datetime
from bs4 import BeautifulSoup
from time import sleep
import requests
import re
import sys
from html.parser import HTMLParser
from projektcheck.utils.spatial import Point


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
        self.html = HTMLParser()
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

        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.findAll('a', {'class': 'uLine'})

        def parse_href_number(tag, href):
            regex = '{tag}=(\d+)!'.format(tag=tag)
            return re.search(regex, href).group(1)

        stops = []

        for row in rows:
            name = row.contents[0]
            if not name:
                continue
            href = row.attrs['href']
            x = int(parse_href_number('X', href))
            y = int(parse_href_number('Y', href))
            id = int(parse_href_number('id', href))
            dist = int(parse_href_number('dist', href))
            stop = Stop(self._from_db_coord(x), self._from_db_coord(y),
                        self.html.unescape(name), distance=dist,
                        id=id, epsg=4326)
            stops.append(stop)

        # response should be sorted by distances in first place,
        # but do it again because you can
        stops_sorted = sorted(stops, key=lambda x: x.distance)
        if n < len(stops_sorted):
            stops_sorted[:n]

        return stops

    def routing(self, origin, destination, times, max_retries=1):
        '''
        times - int or str (e.g. 15 or 15:00)
        '''
        params = self.reiseauskunft_params.copy()
        params['date'] = self.date
        params['S'] = origin
        params['Z'] = destination

        duration = sys.maxint
        departure = mode = ''
        changes = 0

        def request_departure_table(time):
            params['time'] = time
            r = requests.get(self.reiseauskunft_url, params=params,
                             verify=False)
            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find('table', id='resultsOverview')
            return table

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

            rows = table.findAll('tr', {'class': 'firstrow'})

            for row in rows:
                # duration
                content = row.find('td', {'class': 'duration'}).contents
                h, m = content[0].replace('\n', '').split(':')
                d = int(h) * 60 + int(m)
                # if already found shorter duration -> skip
                if d >= duration:
                    continue
                duration = d

                # departure
                content = row.find('td', {'class': 'time'}).contents

                matches = re.findall( r'\d{1,2}:\d{1,2}', ' - '.join(content))
                departure = matches[0] if len(matches) > 0 else ''

                # modes
                content = row.find('td', {'class': 'products'}).contents
                mode = content[0].replace('\n', '')

                # changes
                content = row.find('td', {'class': 'changes'}).contents
                changes = int(content[0].replace('\n', ''))

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
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.findAll('tr', id=lambda x: x and 'journeyRow_' in x)
            n_departures.append(len(rows))
            sleep(self.timeout)

        return n_departures

    def get_timetable_url(self, stop_id):
        params = self.timetable_params.copy()
        params['date'] = self.date
        params['evaId'] = stop_id
        args = ['{}={}'.format(v, k) for v, k in params.iteritems()]
        url = self.timetable_url + u'?' + u'&'.join(args)
        return url
