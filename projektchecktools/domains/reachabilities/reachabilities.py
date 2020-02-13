import webbrowser
from qgis.PyQt.QtWidgets import QMessageBox

from projektchecktools.base.domain import Domain
from projektchecktools.base.tools import FeaturePicker
from projektchecktools.base.project import ProjectLayer
from projektchecktools.base.layers import TileLayer
from projektchecktools.domains.definitions.tables import Projektrahmendaten
from projektchecktools.domains.reachabilities.bahn_query import (
    BahnQuery, StopScraper, BahnRouter, next_working_day)
from projektchecktools.domains.reachabilities.tables import (
    Haltestellen, ErreichbarkeitenOEPNV, Einrichtungen, Isochronen)
from projektchecktools.domains.reachabilities.geoserver_query import (
    EinrichtungenQuery)
from projektchecktools.domains.reachabilities.routing_query import (
    Isochrones)
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.utils.utils import set_category_renderer

#from settings import settings


class Reachabilities(Domain):
    """"""

    ui_label = 'Erreichbarkeiten'
    ui_file = 'ProjektCheck_dockwidget_analysis_02-Err.ui'
    ui_icon = 'images/iconset_mob/20190619_iconset_mob_get_time_stop2central_2.png'

    layer_group = 'Wirkungsbereich 2 - Erreichbarkeit'
    date_format = "%d.%m.%Y"

    def setupUi(self):

        self.ui.stops_button.clicked.connect(self.query_stops)
        #self.ui.show_stops_button.clicked.connect(self.draw_haltestellen)

        self.ui.stops_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_stop(self.ui.stops_combo.currentData()))

        self.ui.show_table_button.clicked.connect(self.show_time_table)
        self.ui.calculate_time_button.clicked.connect(self.calculate_time)
        self.ui.isochrones_button.clicked.connect(self.get_isochrones)
        self.ui.facilities_button.clicked.connect(self.get_einrichtungen)

        self.feature_picker = FeaturePicker(self.ui.pick_stop_button,
                                            canvas=self.canvas)
        self.feature_picker.feature_picked.connect(self.feature_picked)

        self.ui.pick_stop_button.clicked.connect(
            lambda: self.draw_haltestellen(zoom_to=False))

        self.ui.oepnvkarte_button.setCheckable(False)
        self.ui.oepnvkarte_button.clicked.connect(self.oepnv_map)

    def load_content(self):
        self.haltestellen = Haltestellen.features(create=True)\
            .filter(flaechenzugehoerig=True, abfahrten__gt=0)
        self.erreichbarkeiten = ErreichbarkeitenOEPNV.features(create=True)
        self.einrichtungen = Einrichtungen.features(create=True)
        self.isochronen = Isochronen.features(create=True)
        self.project_frame = Projektrahmendaten.features()[0]
        self.stops_layer = None
        self.fill_haltestellen()

    def feature_picked(self, feature):
        self.stops_layer.removeSelection()
        self.stops_layer.select(feature.id())
        fid = feature.id()
        for idx in range(len(self.ui.stops_combo)):
            if fid == self.ui.stops_combo.itemData(idx).id:
                break
        self.ui.stops_combo.setCurrentIndex(idx)

    def toggle_stop(self, stop=None):
        if not stop:
            stop = self.ui.stops_combo.currentData()
        if not stop:
            return
        already_calculated = (stop.berechnet not in ['', '""']
                              and stop.berechnet is not None)
        label = f'Auswertung {stop.berechnet}' if already_calculated \
            else 'noch nicht berechnet'
        self.ui.stop_reach_status_label.setText(label)
        self.ui.recalculate_time_check.setChecked(not already_calculated)
        self.ui.recalculate_time_check.setVisible(already_calculated)
        if self.stops_layer:
            self.stops_layer.removeSelection()
            self.stops_layer.select(stop.id)

    def query_stops(self):
        if not self.ui.recalculatestops_check.isChecked():
            self.draw_haltestellen()
            return

        date = next_working_day()
        job = StopScraper(self.project, date=date, parent=self.ui)
        self.project_frame.haltestellen_berechnet = ''
        self.project_frame.save()

        def on_success(project, date):
            self.draw_haltestellen()
            self.project_frame.haltestellen_berechnet = \
                date.strftime(self.date_format)
            self.project_frame.save()
            self.fill_haltestellen()

        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=lambda project: on_success(project, date))
        dialog.show()

    def fill_haltestellen(self):
        last_calc = self.project_frame.haltestellen_berechnet
        already_calculated = (last_calc not in ['', '""']
                              and last_calc is not None)
        label = f'Auswertung {last_calc}' if already_calculated\
            else 'noch nicht berechnet'
        self.ui.stops_group.setVisible(already_calculated)
        self.ui.recalculatestops_check.setChecked(not already_calculated)
        self.ui.recalculatestops_check.setVisible(already_calculated)
        self.ui.stops_status_label.setText(label)
        self.ui.stops_combo.blockSignals(True)
        self.ui.stops_combo.clear()
        stops = [stop for stop in self.haltestellen]
        stops.sort(key=lambda x: x.name)
        for stop in stops:
            #if stop.abfahrten > 0:
            self.ui.stops_combo.addItem(
                f'{stop.name} ({stop.abfahrten} Abfahrten)', stop)
            #self.ui.stops_status_label
        self.ui.stops_combo.blockSignals(False)
        self.toggle_stop()

    def draw_haltestellen(self, zoom_to=True):
        output = ProjectLayer.from_table(
            self.haltestellen.table, groupname=self.layer_group)
        self.stops_layer = output.draw(
            label='Haltestellen',
            style_file='erreichbarkeit_haltestellen_alt.qml',
            filter='flaechenzugehoerig=1')
        self.feature_picker.set_layer(self.stops_layer)
        if zoom_to:
            output.zoom_to()
        self.toggle_stop()

    def show_time_table(self):
        stop = self.ui.stops_combo.currentData()
        if not stop:
            return
        query = BahnQuery(next_working_day())

        message = QMessageBox()
        message.setIcon(QMessageBox.Information)
        message.setText('Die Abfahrtszeiten werden extern im '
                        'Browser angezeigt!')
        message.setWindowTitle('Haltestellenplan')
        message.exec_()

        url = query.get_timetable_url(stop.id_bahn)
        webbrowser.open(url, new=1, autoraise=True)

    def calculate_time(self):
        stop = self.ui.stops_combo.currentData()
        if not stop:
            return
        recalculate = self.ui.recalculate_time_check.isChecked()
        if not recalculate:
            self.draw_erreichbarkeiten(stop)
            return
        date = next_working_day()
        stop.berechnet = ''
        stop.save()
        job = BahnRouter(stop, self.project, date=date, parent=self.ui)

        def on_success(project, stop, date):
            self.draw_erreichbarkeiten(stop)
            self.ui.recalculate_time_check.setChecked(False)
            stop.berechnet = date.strftime(self.date_format)
            stop.save()
            self.toggle_stop()
            #stop_reach_status_label

        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=lambda project: on_success(project, stop, date))
        dialog.show()

    def draw_erreichbarkeiten(self, stop):
        sub_group = u'Erreichbarkeiten ÖPNV'

        label = f'ab {stop.name}'

        output = ProjectLayer.from_table(
            self.erreichbarkeiten.table,
            groupname=f'{self.layer_group}/{sub_group}')
        output.draw(label=label,
                    style_file='erreichbarkeit_erreichbarkeiten_oepnv.qml',
                    filter=f'id_origin={stop.id}')
        output.zoom_to()

    def get_isochrones(self):
        modus = 'zu Fuß' if self.ui.walk_radio.isChecked() \
            else 'Fahrrad' if self.ui.bike_radio.isChecked() \
            else 'Auto'
        steps = self.ui.timestep_input.value()
        cutoff = self.ui.cutoff_input.value()
        job = Isochrones(self.project, modus=modus, steps=steps, cutoff=cutoff,
                         parent=self.ui)

        def on_success(modus):
            self.draw_isochrones(modus)

        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=lambda x: on_success(modus))
        dialog.show()

    def get_einrichtungen(self):
        radius = self.ui.radius_input.value()
        job = EinrichtungenQuery(self.project, radius=radius, parent=self.ui)
        dialog = ProgressDialog(
            job, parent=self.ui, on_success=lambda r: self.draw_einrichtungen())
        dialog.show()

    def draw_einrichtungen(self):
        sub_group = u'Erreichbarkeiten ÖPNV'

        output = ProjectLayer.from_table(
            self.einrichtungen.table,
            groupname=f'{self.layer_group}/{sub_group}')
        output.draw(label='Einrichtungen',
                    style_file='erreichbarkeit_einrichtungen.qml')
        output.zoom_to()

    def draw_isochrones(self, modus):
        sub_group = f'Erreichbarkeiten'

        output = ProjectLayer.from_table(
            self.isochronen.table,
            groupname=f'{self.layer_group}/{sub_group}')
        end_color = (2, 120, 8) if modus == 'zu Fuß' \
            else (44, 96, 156) if modus == 'Fahrrad' \
            else (64, 56, 56)
        layer = output.draw(label=modus, filter=f'modus="{modus}"')
        output.zoom_to()
        df = self.isochronen.to_pandas()
        set_category_renderer(layer, 'minuten',
                              (255, 255, 255), end_color,
                              unit='Minuten')
        layer.setOpacity(0.8)
        layer.triggerRepaint()

    def oepnv_map(self):
        group = ('Hintergrundkarten')
        url = ('type=xyz&url=http://tile.memomaps.de/tilegen/{z}/{x}/{y}.png'
               '&zmax=18&zmin=0&crs=EPSG:{settings.EPSG}')
        layer = TileLayer(url, groupname=group)
        layer.draw('ÖPNVKarte (memomaps.de)')
        layer.layer.setTitle(
            'Karte memomaps.de CC-BY-SA, Kartendaten Openstreetmap ODbL')