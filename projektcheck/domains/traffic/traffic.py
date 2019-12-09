from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QCursor

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.traffic.tables import TrafficConnector


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
        self.connectors = TrafficConnector.features(create=False)

        self.areas = Teilflaechen.features()
        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        self.ui.area_combo.addItem('Fläche wählen', None)
        for area in self.areas:
            self.ui.area_combo.addItem(area.name, area)
        self.ui.area_combo.blockSignals(False)

        self.show_connectors()
        self.toggle_connector()

        self.connector_tool = QgsMapToolEmitPoint(self.canvas)
        self.connector_tool.canvasClicked.connect(self.map_clicked)
        self.ui.connector_button.clicked.connect(self.toggle_setter)

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

    def toggle_setter(self, active):
        if active:
            self.canvas.setMapTool(self.connector_tool)
            self.canvas.mapToolSet.connect(self.disconnect_setter)
            cursor = QCursor(Qt.CrossCursor)
            self.canvas.setCursor(cursor)
        else:
            self.canvas.unsetMapTool(self.connector_tool)
            self.ui.connector_button.blockSignals(True)
            self.ui.connector_button.setChecked(False)
            self.ui.connector_button.blockSignals(False)

    def disconnect_setter(self, **kwargs):
        self.canvas.mapToolSet.disconnect(self.disconnect_setter)
        self.toggle_setter(False)

    def map_clicked(self, point, e):
        self.connector.geom = point
        # ToDo: transform projection
        self.canvas.refreshAllLayers()
        self.connector.save()


#class ConnectorSetter(QgsMapToolEmitPoint):
    #map_clicked = pyqtSignal(int, int)

    #def canvasReleaseEvent(self, mouseEvent):
        #self.map_clicked.emit(mouseEvent.x(), mouseEvent.y())
