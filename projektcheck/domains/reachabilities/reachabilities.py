from datetime import datetime, date, timedelta
import numpy as np

from projektcheck.base import Domain
from projektcheck.domains.reachabilities.bahn_query import BahnQuery
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
    )
    df_density.sort('Datum', inplace=True)
    # can't compare directly because datetime64 has no length
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
        self.haltestellen_button.clicked.connect(self.query_stops)

    def query_stops(self):
        self.query = BahnQuery(date=next_working_day())
        #arcpy.AddMessage('Berechne die zentralen Orte und Haltestellen '
                             #'in der Umgebung...')
        try:
            self.write_centers_stops()
        except requests.exceptions.ConnectionError:
            print('Die Website der Bahn wurde nicht erreicht. '
                  'Bitte überprüfen Sie Ihre Internetverbindung!')
            return
        #arcpy.AddMessage('Ermittle die Anzahl der Abfahrten je Haltestelle...')
        self.update_departures(projectarea_only=True)

    def write_centers_stops(self):
        '''get centers in radius around project centroid, write their closest
        stops and the stops near the project to the db
        '''
        # truncate tables, will be filled in progress
        self.parent_tbx.delete_rows_in_table('Zentrale_Orte')
        self.parent_tbx.delete_rows_in_table('Haltestellen')

        centroid = get_project_centroid(self.par.projectname.value)
        df_central = self.parent_tbx.table_to_dataframe(
            'Zentrale_Orte_Neu',
            workspace='FGDB_Basisdaten_deutschland.gdb',
            columns=['SHAPE', 'OBJECTID', 'GEN', 'OZ'],
            is_base_table=True
        )
        df_oz = df_central[df_central['OZ'] == 1]
        df_mz = df_central[df_central['OZ'] == 0]

        oz_points = df_oz['SHAPE'].values
        mz_points = df_mz['SHAPE'].values
        oz_points, oz_within = points_within(centroid, oz_points, radius=70000)
        mz_points, mz_within = points_within(centroid, mz_points, radius=30000)
        df_oz_within = df_oz[oz_within]
        df_mz_within = df_mz[mz_within]

        def get_closest_stops(points):
            stops = []
            for point in points:
                t_p = Point(point[0], point[1],
                            epsg=self.parent_tbx.config.epsg)
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
        df_within['id_zentraler_ort'] = df_within['OBJECTID']

        self.parent_tbx.insert_dataframe_in_table('Zentrale_Orte', df_within)

        p_centroid = Point(centroid[0], centroid[1],
                           epsg=self.parent_tbx.config.epsg)
        p_centroid.transform(4326)
        tfl_stops = self.query.stops_near(p_centroid, n=10)

        self._stops_to_db(oz_stops)
        self._stops_to_db(mz_stops)
        self._stops_to_db(tfl_stops, is_project_stop=1)

    def update_departures(self, projectarea_only=False):
        '''update the db-column 'abfahrten' of the stops with the number
        of departures
        '''
        where = 'flaechenzugehoerig = 1' if projectarea_only else None
        df_stops = self.parent_tbx.table_to_dataframe('Haltestellen',
                                                      where=where)
        ids = df_stops['id'].values
        n_departures = self.query.n_departures(ids)
        df_stops['abfahrten'] = n_departures
        self.parent_tbx.dataframe_to_table('Haltestellen', df_stops, ['id'])

    def _stops_to_db(self, stops, is_project_stop=0):
        '''(warning: changes projection of point!)'''
        ids = []
        names = []
        shapes = []
        distances = []

        for stop in stops:
            stop.transform(self.parent_tbx.config.epsg)
            shapes.append(arcpy.Point(stop.x, stop.y))
            ids.append(stop.id)
            names.append(stop.name)
            distances.append(stop.distance)

        column_values = {
            'SHAPE': shapes,
            'id': ids,
            'name': names,
            'flaechenzugehoerig': [is_project_stop] * len(stops),
            'abfahrten': [0] * len(stops),
            'fussweg': distances
        }

        self.parent_tbx.insert_rows_in_table('Haltestellen',
                                             column_values=column_values)
