from qgis.PyQt.QtCore import Qt
from qgis.PyQt.Qt import (QSpacerItem, QSizePolicy,
                          QVBoxLayout, QWidget)
import os

from projektchecktools.base.domain import Domain
from projektchecktools.utils.utils import clear_layout
from projektchecktools.base.project import ProjectLayer
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.domains.traffic.tables import (
    Links, Itineraries, TransferNodes, Ways)
from projektchecktools.domains.traffic.routing import Routing
from projektchecktools.base.params import (Params, Param, Title,
                                           Seperator, SumDependency)
from projektchecktools.base.inputs import (SpinBox, Slider)
from projektchecktools.domains.constants import Nutzungsart
from projektchecktools.utils.utils import open_file


class Traffic(Domain):
    """"""

    ui_label = 'Verkehr im Umfeld'
    ui_file = 'domain_03-ViU.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_traffic_6.png"

    layer_group = "Wirkungsbereich 3 - Verkehr im Umfeld"

    @classmethod
    def reset(cls, project=None):
        if not project:
            project = cls.project_manager.active_project
        nodes = TransferNodes.features(project=project, create=True)
        nodes.delete()

    def setupUi(self):
        self.ui.calculate_traffic_button.clicked.connect(
            self.calculate_traffic)

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Verkehr_im_Umfeld.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

    def load_content(self):
        super().load_content()
        self.params = None
        output = ProjectLayer.find('Projektdefinition')
        if output:
            output[0].setItemVisibilityChecked(True)
        self.links = Links.features(project=self.project, create=True)
        self.transfer_nodes = TransferNodes.features(project=self.project,
                                                     create=True)
        self.itineraries = Itineraries.features(project=self.project, create=True)
        self.ways = Ways.features(project=self.project, create=True)

        self.ui.distance_frame.setVisible(False)
        if len(self.transfer_nodes) == 0:
            self.ui.recalculate_check.setChecked(True)
            self.ui.recalculate_check.setVisible(False)
            # there is a signal for that in the ui file, but it isn't working
            # if checkbox is already invisible
            self.ui.distance_frame.setVisible(True)
        self.setup_settings()

    def setup_settings(self):
        if self.params:
            self.params.close()
        layout = self.ui.settings_group.layout()
        clear_layout(layout)
        #QWidget().setLayout(layout)
        #layout = QVBoxLayout(self.ui.settings_group)
        self.params = Params(parent=layout, button_label='Annahmen verändern',
                             help_file='verkehr_wege_gewichtungen.txt')

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

        dependency = SumDependency(100)
        for node in self.transfer_nodes:
            perc = round(node.weight)
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

        job = Routing(self.project, recalculate=True)
        def on_success(res):
            self.draw_traffic()
            self.setup_settings()
        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=on_success
        )
        dialog.show()

    def calculate_traffic(self):
        distance = self.ui.distance_input.value()
        recalculate = self.ui.recalculate_check.isChecked()
        if recalculate:
            tree_layer = ProjectLayer.find(self.layer_group)
            if tree_layer:
                tree_layer[0].removeAllChildren()
            job = Routing(self.project,
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
            dialog.show()
        else:
            self.draw_traffic()

    def draw_traffic(self):
        output = ProjectLayer.from_table(self.transfer_nodes.table,
                                         groupname=self.layer_group)
        output.draw(label='Zielpunkte',
                    style_file='verkehr_zielpunkte.qml')

        output = ProjectLayer.from_table(self.links.table,
                                         groupname=self.layer_group)
        output.draw(label='Zusätzliche PKW-Fahrten',
                    style_file='verkehr_links_zusaetzliche_PKW-Fahrten.qml')

        output = ProjectLayer.from_table(self.itineraries.table,
                                         groupname=self.layer_group)
        output.draw(label='kürzeste Wege',
                    style_file='verkehr_kuerzeste_Wege.qml', expanded=False)

        output.zoom_to()

    def close(self):
        if hasattr(self, 'params'):
            self.params.close()
        super().close()