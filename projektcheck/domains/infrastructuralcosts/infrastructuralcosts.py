from projektcheck.base.domain import Domain
from projektcheck.base.tools import LineMapTool
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.infrastructuralcosts.tables import (
    ErschliessungsnetzLinien, ErschliessungsnetzPunkte)
from projektcheck.base.tools import FeaturePicker, MapClickedTool


class InfrastructureDrawing:
    def __init__(self, parent):
        self.parent = parent

        self.parent.ui.show_lines_button.clicked.connect(
            lambda: self.draw_output('line'))
        self.parent.ui.show_points_button.clicked.connect(
            lambda: self.draw_output('point'))
        self.setup_tools()

    def load_content(self):
        self.output_lines = ProjectLayer.from_table(
            self.parent.lines.table, groupname=self.parent.layer_group,
            prepend=True)
        self.output_points = ProjectLayer.from_table(
            self.parent.points.table, groupname=self.parent.layer_group,
            prepend=True)

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
            button.clicked.connect(lambda: self.draw_output('line'))
            tool = LineMapTool(button, canvas=self.parent.canvas)
            tool.drawn.connect(
                lambda geom, i=net_id: self.add_geom(geom, i, geom_typ='line'))

        self.select_lines_tool = FeaturePicker(
            self.parent.ui.select_lines_button, canvas=self.parent.canvas)
        self.parent.ui.select_lines_button.clicked.connect(
            lambda: self.draw_output('line'))
        self.select_lines_tool.feature_picked.connect(self.line_selected)
        self.parent.ui.remove_lines_button.clicked.connect(
            self.remove_selected_lines)

        self.draw_point_tool = MapClickedTool(
            self.parent.ui.add_point_button, canvas=self.parent.canvas)
        self.draw_point_tool.map_clicked.connect(self.add_point)

    def add_geom(self, geom, net_id, geom_typ='line'):
        features = self.parent.lines if geom_typ == 'line' \
            else self.parent.points
        feature = features.add(IDNetzelement=net_id, geom=geom)
        if len(features) == 1:
            self.draw_output(geom_typ, redraw=True)
        self.parent.canvas.refreshAllLayers()
        return feature

    def draw_output(self, geom_typ='line', redraw=False):
        label = 'Erschließungsnetz'
        if geom_typ == 'point':
            label += ' - punktuelle Maßnahmen'
        output = self.output_lines if geom_typ == 'line' else self.output_points
        style = 'kosten_erschliessungsnetze_{}elemente.qml'.format(
            'linien' if geom_typ == 'line' else 'punkt')
        output.draw(label=label, style_file=style, redraw=redraw)
        if geom_typ == 'line':
            self.select_lines_tool.set_layer(output.layer)

    def line_selected(self, feature):
        layer = self.output_lines.layer
        selected = [f.id() for f in layer.selectedFeatures()]
        if feature.id() not in selected:
            layer.select(feature.id())
        else:
            layer.removeSelection()
            layer.selectByIds([fid for fid in selected if fid != feature.id()])

    def remove_selected_lines(self):
        layer = self.output_lines.layer
        for qf in layer.selectedFeatures():
            feat = self.parent.lines.get(id=qf.id())
            feat.delete()
        self.parent.canvas.refreshAllLayers()

    def add_point(self, geom):
        feature = self.add_geom(geom, 1, geom_typ='point')
        feature.bezeichnung = 'unbenannt'
        feature.save()
        #self.parent.points.add(bezeichnung='unbenannt', geom=geom)


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
