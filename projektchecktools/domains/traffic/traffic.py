from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.Qt import QSpacerItem, QSizePolicy
from qgis.PyQt.QtWidgets import QVBoxLayout

from projektchecktools.base.domain import Domain
from projektchecktools.utils.utils import clearLayout
from projektchecktools.base.project import ProjectLayer
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.base.tools import MapClickedTool
from projektchecktools.domains.definitions.tables import Teilflaechen
from projektchecktools.domains.traffic.tables import (Connectors, Links,
                                                 TransferNodes, Ways)
from projektchecktools.domains.traffic.routing import Routing
from projektchecktools.base.params import (Params, Param, Title,
                                      Seperator, SumDependency)
from projektchecktools.base.inputs import (SpinBox, Slider)
from projektchecktools.domains.constants import Nutzungsart


class Traffic(Domain):
    """"""

    ui_label = 'Verkehr im Umfeld'
    ui_file = 'ProjektCheck_dockwidget_analysis_03-ViU.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_traffic_6.png"

    layer_group = "Wirkungsbereich 3 - Verkehr im Umfeld"

    @classmethod
    def reset(cls, project=None):
        if not project:
            project = cls.project_manager.active_project
        nodes = TransferNodes.features(project=project, create=True)
        nodes.delete()

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_connector(self.ui.area_combo.currentData()))
        self.connector_tool = MapClickedTool(self.ui.connector_button,
                                             canvas=self.canvas,
                                             target_crs=self.settings.EPSG)
        self.connector_tool.map_clicked.connect(self.map_clicked)
        self.ui.calculate_traffic_button.clicked.connect(
            self.calculate_traffic)

    def load_content(self):
        self.connectors = Connectors.features(create=False)
        self.links = Links.features(project=self.project, create=True)
        self.transfer_nodes = TransferNodes.features(project=self.project,
                                                     create=True)
        self.ways = Ways.features(project=self.project, create=True)
        self.areas = Teilflaechen.features()

        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        self.ui.area_combo.addItem('Fläche wählen', None)
        for area in self.areas:
            self.ui.area_combo.addItem(area.name, area)
        self.ui.area_combo.blockSignals(False)

        self.show_connectors()
        self.toggle_connector()

        self.ui.distance_frame.setVisible(False)
        if len(self.transfer_nodes) == 0:
            self.ui.recalculate_check.setChecked(True)
            self.ui.recalculate_check.setVisible(False)
            # there is a signal for that in the ui file, but it isn't working
            # if checkbox is already invisible
            self.ui.distance_frame.setVisible(True)
        self.params = None
        self.setup_settings()

    def setup_settings(self):
        layout = self.ui.settings_group.layout()
        if not layout:
            layout = QVBoxLayout()
            self.ui.settings_group.setLayout(layout)
        else:
            clearLayout(layout)
        if self.params:
            self.params.close()
        self.params = Params(parent=layout, button_label='Annahmen verändern',
                             help_file='verkehr_wege_gewichtungen.txt')
        if len(self.transfer_nodes) == 0:
            # workaround: otherwise the params don't show later (don't know why)
            self.params.show()
            return

        self.params.add(Title('Verkehrsaufkommen und Verkehrsmittelwahl'))
        for i, way in enumerate(self.ways):
            name = Nutzungsart(way.nutzungsart).name.capitalize()
            self.params.add(Title(name, fontsize=8))
            self.params[f'{name}_gesamt'] = Param(
                way.wege_gesamt, SpinBox(),
                label='Gesamtanzahl der Wege pro Werktag (Hin- und Rückwege)')
            self.params[f'{name}_miv'] = Param(
                way.miv_anteil, SpinBox(maximum=100),
                label='Anteil der von Pkw-Fahrenden gefahrenen Wegen', unit='%')
            if i != len(self.ways) - 1:
                self.params.add(Seperator(margin=0))

        spacer = QSpacerItem(
            10, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.params.add(spacer)

        self.params.add(Title('Gewichtung der Herkunfts-/Zielpunkte'))

        sum_weights = 0
        for node in self.transfer_nodes:
            sum_weights += node.weight

        dependency = SumDependency(100)
        for node in self.transfer_nodes:
            perc = round(100 * node.weight / sum_weights)
            node.save()
            param = Param(
                perc,
                Slider(maximum=100, lockable=True),
                label=node.name, unit='%'
            )
            self.params.add(param, name=node.name)
            dependency.add(param)

        self.params.changed.connect(self.save_settings)
        self.params.show()

    def save_settings(self):
        sum_weights = 0
        for node in self.transfer_nodes:
            sum_weights += node.weight

        for node in self.transfer_nodes:
            node.weight = self.params[node.name].value * sum_weights / 100
            node.save()

        for way in self.ways:
            name = Nutzungsart(way.nutzungsart).name.capitalize()
            way.miv_anteil = self.params[f'{name}_miv'].value
            way.wege_gesamt = self.params[f'{name}_gesamt'].value
            way.save()

        job = Routing(self.project, parent=self.ui, recalculate=True)
        def on_success(res):
            self.draw_traffic()
            self.setup_settings()
        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=on_success
        )
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.show()

    def show_connectors(self):
        output = ProjectLayer.from_table(
            self.connectors.table, groupname=self.layer_group)
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
        recalculate = self.ui.recalculate_check.isChecked()
        if recalculate:
            job = Routing(self.project, # parent=self.ui,
                          distance=distance)
            def on_success(res):
                self.ui.recalculate_check.setVisible(True)
                self.ui.recalculate_check.setChecked(False)
                self.draw_traffic()
                self.setup_settings()
            dialog = ProgressDialog(
                job, parent=self.ui,
                on_success=on_success
            )
            dialog.setAttribute(Qt.WA_DeleteOnClose)
            dialog.show()
        else:
            self.draw_traffic()

    def draw_traffic(self):
        output = ProjectLayer.from_table(self.links.table,
                                         groupname=self.layer_group)
        output.draw(label='Zusätzliche PKW-Fahrten',
                    style_file='verkehr_links_zusaetzliche_PKW-Fahrten.qml')

        output = ProjectLayer.from_table(self.transfer_nodes.table,
                                         groupname=self.layer_group)
        output.draw(label='Zielpunkte',
                    style_file='verkehr_zielpunkte.qml')
        output.zoom_to()