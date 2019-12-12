from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QCursor

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.base.dialogs import ProgressDialog
from projektcheck.base.tools import MapClickedTool
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.traffic.tables import (Connectors, Links, Nodes,
                                                 TransferNodes)
from projektcheck.domains.traffic.routing import Routing

import settings


class Traffic(Domain):
    """"""

    ui_label = 'Verkehr im Umfeld'
    ui_file = 'ProjektCheck_dockwidget_analysis_03-ViU.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_traffic_6.png"

    layer_group = "Wirkungsbereich 3 - Verkehr im Umfeld"

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_connector(self.ui.area_combo.currentData()))

    def load_content(self):
        self.connectors = Connectors.features(create=False)
        self.links = Links.features(project=self.project, create=True)
        self.transfer_nodes = TransferNodes.features(project=self.project,
                                                     create=True)

        self.areas = Teilflaechen.features()
        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        self.ui.area_combo.addItem('Fläche wählen', None)
        for area in self.areas:
            self.ui.area_combo.addItem(area.name, area)
        self.ui.area_combo.blockSignals(False)

        self.show_connectors()
        self.toggle_connector()

        self.connector_tool = MapClickedTool(self.ui.connector_button,
                                             canvas=self.canvas,
                                             target_crs=self.settings.EPSG)
        self.connector_tool.map_clicked.connect(self.map_clicked)
        self.ui.calculate_traffic_button.clicked.connect(
            self.calculate_traffic)

    def show_connectors(self):
        output = ProjectLayer.from_table(
            self.connectors._table, groupname=self.layer_group)
        self.connector_layer = output.draw(
            label='Anbindungspunkte',
            style_file='verkehr_anbindungspunkte.qml')

    def toggle_connector(self, area=None):
        self.connector = None
        if not self.connector_layer:
            return
        self.connector_layer.removeSelection()
        if area:
            self.connector = self.connectors.get(id_teilflaeche=area.id)
            self.connector_layer.select(self.connector.id)

    def map_clicked(self, geom):
        if not self.connector:
            return
        self.connector.geom = geom
        self.canvas.refreshAllLayers()
        self.connector.save()

    def calculate_traffic(self):
        distance = self.ui.distance_input.value()
        job = Routing(self.project, distance=distance, parent=self.ui)

        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=lambda result: self.draw_traffic())
        dialog.show()

    def draw_traffic(self):

        output = ProjectLayer.from_table(self.transfer_nodes._table,
                                         groupname=self.layer_group)
        output.draw(label='Zielpunkte',
                    style_file='verkehr_zielpunkte.qml')
        output.zoom_to()

        output = ProjectLayer.from_table(self.links._table,
                                         groupname=self.layer_group)
        output.draw(label='Zusätzliche PKW-Fahrten',
                    style_file='verkehr_links_zusaetzliche_PKW-Fahrten.qml')
        output.zoom_to()
