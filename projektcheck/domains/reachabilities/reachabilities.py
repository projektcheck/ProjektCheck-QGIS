import webbrowser
from qgis.PyQt.QtWidgets import QMessageBox

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
from projektcheck.utils.utils import add_selection_icons
from settings import settings


class Reachabilities(Domain):
    """"""

    ui_label = 'Erreichbarkeiten'
    ui_file = 'ProjektCheck_dockwidget_analysis_02-Err.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_get_time_stop2central_2.png"

    layer_group = "Wirkungsbereich 2 - Erreichbarkeit"

    def setupUi(self):
        add_selection_icons(self.ui.toolBox)

        self.ui.haltestellen_button.clicked.connect(self.query_stops)
        self.ui.show_haltestellen_button.clicked.connect(self.draw_haltestellen)
        self.ui.haltestellen_combo.currentIndexChanged.connect(
            lambda index: self.zoom_to(
                self.ui.haltestellen_combo.itemData(index)))

        self.ui.show_table_button.clicked.connect(self.show_time_table)
        self.ui.calculate_time_button.clicked.connect(self.calculate_time)
        self.ui.isochrones_button.clicked.connect(self.get_isochrones)
        self.ui.facilities_button.clicked.connect(self.get_einrichtungen)

    def load_content(self):
        self.haltestellen = Haltestellen.features(create=True)
        self.erreichbarkeiten = ErreichbarkeitenOEPNV.features(create=True)
        self.einrichtungen = Einrichtungen.features(create=True)
        self.isochronen = Isochronen.features(create=True)
        self.fill_haltestellen()

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
        self.ui.haltestellen_combo.blockSignals(True)
        self.ui.haltestellen_combo.clear()
        self.haltestellen.filter(flaechenzugehoerig=True)
        for stop in self.haltestellen:
            if stop.abfahrten > 0:
                self.ui.haltestellen_combo.addItem(stop.name, stop)
        self.haltestellen.filter()
        self.ui.haltestellen_combo.blockSignals(False)

    def draw_haltestellen(self):
        output = ProjectLayer.from_table(
            self.haltestellen._table, groupname=self.layer_group)
        output.draw(label='Haltestellen',
                    style_file='erreichbarkeit_haltestellen.qml',
                    filter='flaechenzugehoerig=1')
        output.zoom_to()

    def show_time_table(self):
        stop = self.ui.haltestellen_combo.currentData()
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
        stop = self.ui.haltestellen_combo.currentData()
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
        output.draw(label=modus, filter=f'modus="{modus}"')
        output.zoom_to()

        #group_layer = ("erreichbarkeit")
        #layers = ['Isochrone zu Fuß',
                  #'Isochrone Fahrrad',
                  #'Isochrone Auto']
        #fc = u'Isochrone'
        #for layer in layers:
            #name = layer
            ## ToDo: get cutoff time from db instead of from run()
            #if self.cutoff:
                #name += ' ({} Minuten)'.format(self.cutoff)
            #self.output.add_layer(group_layer, layer, fc,
                                  #name=name,
                                  #template_folder='Erreichbarkeit',
                                  #zoom=False)
