from projektcheck.base.domain import Domain
from projektcheck.base.tools import LineMapTool
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.infrastructuralcosts.tables import (
    ErschliessungsnetzLinien, ErschliessungsnetzPunkte)


class InfrastructureDrawing:
    def __init__(self, parent):
        self.parent = parent
        self.setup_tools()

    def load_content(self):
        self.output_lines = ProjectLayer.from_table(
            self.parent.lines.table, groupname=self.parent.layer_group,
            prepend=True)
        self.output_points = ProjectLayer.from_table(
            self.parent.points.table, groupname=self.parent.layer_group,
            prepend=True)
        self.draw_output('line')
        self.draw_output('point')

    def setup_tools(self):
        self.line_tools = {
            self.parent.ui.anliegerstrasse_innere_button: 11,
            self.parent.ui.sammelstrasse_innere_button: 12,
            self.parent.ui.anliegerstrasse_aeussere_button: 21,
            self.parent.ui.sammelstrasse_aeussere_button: 22,
            self.parent.ui.kanal_trennsystem_button: 31,
            self.parent.ui.kanal_mischsystem_button: 32,
            self.parent.ui.kanal_schmutzwasser_button: 33,
            self.parent.ui.trinkwasserleitung_button: 41,
            self.parent.ui.stromleitung_button: 51
        }

        for button, net_id in self.line_tools.items():
            tool = LineMapTool(button, canvas=self.parent.canvas)
            tool.drawn.connect(
                lambda geom, i=net_id: self.add_geom(geom, i, geom_typ='line'))

    def add_geom(self, geom, net_id, geom_typ='line'):
        features = self.parent.lines if geom_typ == 'line' \
            else self.parent.points
        features.add(IDNetzelement=net_id, geom=geom)
        if len(features) == 1:
            self.draw_output(geom_typ)

    def draw_output(self, geom_typ='line'):
        label = 'Erschließungsnetz'
        if geom_typ == 'point':
            label += ' - punktuelle Maßnahmen'
        output = self.output_lines if geom_typ == 'line' else self.output_points
        style = 'kosten_erschliessungsnetze_{}elemente.qml'.format(
            'linien' if geom_typ == 'line' else 'punkt')
        output.draw(label=label, style_file=style)


class InfrastructuralCosts(Domain):
    """"""

    ui_label = 'Infrastrukturfolgekosten'
    ui_file = 'ProjektCheck_dockwidget_analysis_06-IFK.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_infrstucturalcosts_4.png"

    layer_group = 'Wirkungsbereich 6 - Infrastrukturfolgekosten'

    def setupUi(self):
        self.drawing = InfrastructureDrawing(self)

    def load_content(self):
        self.lines = ErschliessungsnetzLinien.features(create=True)
        self.points = ErschliessungsnetzPunkte.features(create=True)
        self.drawing.load_content()
