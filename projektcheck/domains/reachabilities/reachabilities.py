import webbrowser
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QCursor
from qgis.core import QgsVectorLayer, QgsFeature
from qgis.gui import QgsMapToolIdentify

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.reachabilities.bahn_query import (
    BahnQuery, StopScraper, BahnRouter, next_working_day)
from projektcheck.domains.reachabilities.tables import (
    Haltestellen, ErreichbarkeitenOEPNV, Einrichtungen, Isochronen)
from projektcheck.domains.reachabilities.geoserver_query import (
    EinrichtungenQuery)
from projektcheck.domains.reachabilities.routing_query import (
    Isochrones)
from projektcheck.base.dialogs import ProgressDialog
from projektcheck.utils.utils import add_selection_icons, set_category_renderer
from settings import settings


class Reachabilities(Domain):
    """"""

    ui_label = 'Erreichbarkeiten'
    ui_file = 'ProjektCheck_dockwidget_analysis_02-Err.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_get_time_stop2central_2.png"

    layer_group = "Wirkungsbereich 2 - Erreichbarkeit"

    def setupUi(self):
        add_selection_icons(self.ui.toolBox)

        self.ui.stops_button.clicked.connect(self.query_stops)
        self.ui.show_stops_button.clicked.connect(self.draw_haltestellen)

        self.ui.stops_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_stop(self.ui.stops_combo.currentData()))

        self.ui.show_table_button.clicked.connect(self.show_time_table)
        self.ui.calculate_time_button.clicked.connect(self.calculate_time)
        self.ui.isochrones_button.clicked.connect(self.get_isochrones)
        self.ui.facilities_button.clicked.connect(self.get_einrichtungen)

        self.feature_picker = FeaturePicker(self.canvas)
        self.feature_picker.feature_picked.connect(self.feature_picked)
        self.ui.pick_stop_button.clicked.connect(self.toggle_picker)

    def load_content(self):
        self.haltestellen = Haltestellen.features(create=True)
        self.erreichbarkeiten = ErreichbarkeitenOEPNV.features(create=True)
        self.einrichtungen = Einrichtungen.features(create=True)
        self.isochronen = Isochronen.features(create=True)
        self.fill_haltestellen()
        self.stops_layer = None

    def disconnect_picker(self, **kwargs):
        self.canvas.mapToolSet.disconnect(self.disconnect_picker)
        self.toggle_picker(False)

    def toggle_picker(self, active):
        if active:
            self.draw_haltestellen()
            self.canvas.setMapTool(self.feature_picker)
            self.canvas.mapToolSet.connect(self.disconnect_picker)
            cursor = QCursor(Qt.CrossCursor)
            self.canvas.setCursor(cursor)
        else:
            self.canvas.unsetMapTool(self.feature_picker)
            self.ui.pick_stop_button.blockSignals(True)
            self.ui.pick_stop_button.setChecked(False)
            self.ui.pick_stop_button.blockSignals(False)

    def feature_picked(self, layer, feature):
        if layer.name() == 'Haltestellen':
            layer.removeSelection()
            layer.select(feature.id())
            name = feature.attribute('name')
            self.ui.stops_combo.setCurrentText(name)

    def toggle_stop(self, stop):
        if not self.stops_layer or not stop:
            return
        self.stops_layer.removeSelection()
        self.stops_layer.select(stop.id)

    def query_stops(self):
        job = StopScraper(self.project, parent=self.ui)

        def on_success(project):
            self.draw_haltestellen()
            self.fill_haltestellen()

        dialog = ProgressDialog(job, parent=self.ui,
                                on_success=on_success)
        dialog.show()

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
        self.ui.stops_combo.blockSignals(True)
        self.ui.stops_combo.clear()
        self.haltestellen.filter(flaechenzugehoerig=True)
        for stop in self.haltestellen:
            if stop.abfahrten > 0:
                self.ui.stops_combo.addItem(stop.name, stop)
        self.haltestellen.filter()
        self.ui.stops_combo.blockSignals(False)

    def draw_haltestellen(self):
        output = ProjectLayer.from_table(
            self.haltestellen._table, groupname=self.layer_group)
        self.stops_layer = output.draw(
            label='Haltestellen',
            style_file='erreichbarkeit_haltestellen.qml',
            filter='flaechenzugehoerig=1')
        output.zoom_to()
        self.toggle_stop(self.ui.stops_combo.currentData())

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
        recalculate = self.ui.recalculate_check.isChecked()
        job = BahnRouter(stop, self.project, parent=self.ui,
                         recalculate=recalculate)

        def on_success(project, stop):
            self.draw_erreichbarkeiten(stop)

        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=lambda project: on_success(project, stop))
        dialog.show()

    def draw_erreichbarkeiten(self, stop):
        sub_group = u'Erreichbarkeiten ÖPNV'

        label = f'ab {stop.name}'

        output = ProjectLayer.from_table(
            self.erreichbarkeiten._table,
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
            self.einrichtungen._table,
            groupname=f'{self.layer_group}/{sub_group}')
        output.draw(label='Einrichtungen',
                    style_file='erreichbarkeit_einrichtungen.qml')
        output.zoom_to()

    def draw_isochrones(self, modus):
        sub_group = f'Erreichbarkeiten'

        output = ProjectLayer.from_table(
            self.isochronen._table,
            groupname=f'{self.layer_group}/{sub_group}')
        end_color = (2, 120, 8) if modus == 'zu Fuß' \
            else (44, 96, 156) if modus == 'Fahrrad' \
            else (64, 56, 56)
        layer = output.draw(label=modus, filter=f'modus="{modus}"')
        output.zoom_to()
        df = self.isochronen.to_pandas()
        values = df['sekunden'].unique()
        set_category_renderer(layer, 'sekunden',
                              (255, 255, 255), end_color,
                              unit='Sekunden')
        layer.setOpacity(0.8)
        layer.triggerRepaint()


class FeaturePicker(QgsMapToolIdentify):
    feature_picked = pyqtSignal(QgsVectorLayer, QgsFeature)

    def canvasReleaseEvent(self, mouseEvent):
        results = self.identify(mouseEvent.x(), mouseEvent.y(),
                                self.LayerSelection, self.VectorLayer)
        if len(results) > 0:
            self.feature_picked.emit(results[0].mLayer,
                                    QgsFeature(results[0].mFeature))
