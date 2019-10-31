import webbrowser
from qgis.PyQt.QtWidgets import QMessageBox

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.reachabilities.bahn_query import (BahnQuery,
                                                            StopScraper,
                                                            BahnRouter,
                                                            next_working_day)
from projektcheck.domains.reachabilities.tables import Haltestellen
from projektcheck.base.dialogs import ProgressDialog
from projektcheck.utils.utils import add_selection_icons
from settings import settings


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
        self.ui.calculate_time_button.clicked.connect(
            lambda: self.calculate_time(
                self.ui.haltestellen_combo.currentData()))

    def load_content(self):
        self.haltestellen = Haltestellen.features(create=True)
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
            self.ui.haltestellen_combo.addItem(stop.name, stop)
        self.haltestellen.filter()
        self.ui.haltestellen_combo.blockSignals(False)

    def draw_haltestellen(self):
        output = ProjectLayer.from_table(
            self.haltestellen._table, groupname='Erreichbarkeiten')
        output.draw(label='Haltestellen',
                    style_file='erreichbarkeit_haltestellen.qml',
                    filter='flaechenzugehoerig=1')
        output.zoom_to()

    def show_time_table(self, stop):
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

    def calculate_time(self, stop):
        job = BahnRouter(stop, self.project, parent=self.ui)

        def on_success(project):
            pass
            #self.draw_haltestellen()
            #self.fill_haltestellen()

        dialog = ProgressDialog(job, parent=self.ui,
                                on_success=on_success)
        dialog.show()
