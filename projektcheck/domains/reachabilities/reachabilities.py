from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
import requests
import webbrowser
from qgis.PyQt.QtWidgets import QMessageBox

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.reachabilities.bahn_query import BahnQuery
from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.domains.reachabilities.tables import (Haltestellen,
                                                        ZentraleOrte)
from projektcheck.utils.spatial import points_within, Point
from projektcheck.utils.utils import add_selection_icons
from settings import settings

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
    df_density = basedata.get_table(
        'Feriendichte', 'Basisdaten_deutschland'
    ).to_pandas()
    # can't compare directly because datetime64 has no length
    dates = pd.to_datetime(df_density['Datum'], format='%Y/%m/%d %H:%M:%S.%f')
    df_density['Datum'] = dates.dt.tz_convert(None)
    df_density.sort_values('Datum', inplace=True)
    infront = np.where(df_density['Datum'] >= day)[0]
    if len(infront) > 0:
        # get the first day matching all conditions
        day = df_density.iloc[infront[0]]['Datum']
    return pd.Timestamp(day).date()


class Reachabilities(Domain):
    """"""

    ui_label = 'Erreichbarkeiten'
    ui_file = 'ProjektCheck_dockwidget_analysis_02-Err.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_get_time_stop2central_2.png"

    def setupUi(self):
        add_selection_icons(self.ui.toolBox)

        self.ui.haltestellen_button.clicked.connect(self.query_stops)
        self.ui.show_haltestellen_button.clicked.connect(self.draw_haltestellen)
        self.ui.haltestellen_combo.currentIndexChanged.connect(
            lambda index: self.zoom_to(
                self.ui.haltestellen_combo.itemData(index)))

        self.ui.show_table_button.clicked.connect(
            lambda: self.show_time_table(
                self.ui.haltestellen_combo.currentData()))
        self.ui.calculate_time_button.clicked.connect(self.calculate_time)

    def load_content(self):
        self.haltestellen = Haltestellen.features(create=True)
        self.zentrale_orte = ZentraleOrte.features(create=True)
        self.fill_haltestellen()

    def zoom_to(self, feature):
        if not feature:
            return
        #target_srid = self.canvas.mapSettings().destinationCrs().authid()
        #point = feature.geom.asPoint()
        #point = Point(point.x(), point.y(), epsg=settings.EPSG)
        #point.transform(target_srid)
        #self.canvas.zoomWithCenter(point.x, point.y, False)
        # ToDo: get layer and zoom to
        #self.canvas.zoomToSelected(layer)

    def fill_haltestellen(self):
        self.ui.haltestellen_combo.blockSignals(True)
        self.ui.haltestellen_combo.clear()
        self.haltestellen.filter(flaechenzugehoerig=True)
        for stop in self.haltestellen:
            self.ui.haltestellen_combo.addItem(stop.name, stop)
        self.haltestellen.filter()
        self.ui.haltestellen_combo.blockSignals(False)

    def query_stops(self):
        self.query = BahnQuery(date=next_working_day())
        #arcpy.AddMessage('Berechne die zentralen Orte und Haltestellen '
                             #'in der Umgebung...')
        try:
            self.write_centers_stops()
        except requests.exceptions.ConnectionError:
            print('Die Website der Bahn ist nicht erreichbar')
            return
        #arcpy.AddMessage('Ermittle die Anzahl der Abfahrten je Haltestelle...')
        self.update_departures(projectarea_only=True)
        self.draw_haltestellen()
        self.fill_haltestellen()

    def draw_haltestellen(self):
        output = ProjectLayer.from_table(
            self.haltestellen._table, groupname='Projektdefinition')
        output.draw(label='Haltestellen',
                    style_file='erreichbarkeit_haltestellen.qml')

    def write_centers_stops(self):
        '''get centers in radius around project centroid, write their closest
        stops and the stops near the project to the db
        '''
        # truncate tables, will be filled in progress
        self.haltestellen.delete()
        self.zentrale_orte.delete()

        project_frame = Projektrahmendaten.features()[0]
        centroid = project_frame.geom.asPoint()
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

    def show_time_table(self, stop):
        if not stop:
            return
        query = BahnQuery(next_working_day())

        message = QMessageBox()
        message.setIcon(QMessageBox.Information)
        message.setText('Die Abfahrtszeiten werden extern im '
                        'Browser angezeigt!')
        message.setWindowTitle('Fahrplan')
        message.exec_()

        url = query.get_timetable_url(stop.id_bahn)
        webbrowser.open(url, new=1, autoraise=True)

    def calculate_time(self):
        pass
