from projektcheck.base.domain import Domain
from projektcheck.base.tools import LineMapTool
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.infrastructuralcosts.tables import (
    ErschliessungsnetzLinien, ErschliessungsnetzPunkte)
from projektcheck.base.tools import FeaturePicker, MapClickedTool
from projektcheck.utils.utils import clearLayout
from projektcheck.base.params import (Params, Param, Title, Seperator)
from projektcheck.base.inputs import (SpinBox, ComboBox, LineEdit, Checkbox,
                                      Slider, DoubleSpinBox)


class InfrastructureDrawing:
    def __init__(self, parent):
        self.parent = parent

        self.parent.ui.show_lines_button.clicked.connect(
            lambda: self.draw_output('line'))
        self.parent.ui.show_lines_button.setCheckable(False)
        self.parent.ui.show_points_button.clicked.connect(
            lambda: self.draw_output('point'))
        self.parent.ui.show_points_button.setCheckable(False)

        self.parent.ui.points_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_point(
                self.parent.ui.points_combo.currentData()))
        #self.parent.ui.points_combo.currentIndexChanged.connect(
            #lambda: self.draw_output('point'))

        self.parent.ui.remove_point_button.clicked.connect(self.remove_point)

        self.setup_tools()

    def load_content(self):
        self.output_lines = ProjectLayer.from_table(
            self.parent.lines.table, groupname=self.parent.layer_group,
            prepend=True)
        self.output_points = ProjectLayer.from_table(
            self.parent.points.table, groupname=self.parent.layer_group,
            prepend=True)
        self.fill_points_combo()

    def fill_points_combo(self, select=None):
        self.parent.ui.points_combo.blockSignals(True)
        self.parent.ui.points_combo.clear()
        points = [point for point in self.parent.points]
        points.sort(key=lambda x: x.IDNetzelement)
        idx = 0
        for i, point in enumerate(points):
            # ToDo: show netztyp name in combo
            typ = self.parent.netzelemente.get(
                IDNetzelement=point.IDNetzelement)
            self.parent.ui.points_combo.addItem(
                f'{point.bezeichnung} ({typ.Netzelement if typ else "-"})',
                point)
            if select and point.id == select.id:
                idx = i
        if idx:
            self.parent.ui.points_combo.setCurrentIndex(idx)
        self.parent.ui.points_combo.blockSignals(False)
        self.toggle_point()

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
        self.select_point_tool = FeaturePicker(
            self.parent.ui.select_point_button, canvas=self.parent.canvas)
        self.select_point_tool.feature_picked.connect(self.point_selected)
        self.parent.ui.select_point_button.clicked.connect(
            lambda: self.draw_output('point'))
        self.parent.ui.add_point_button.clicked.connect(
            lambda: self.draw_output('point'))

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
        tool = self.select_lines_tool if geom_typ == 'line' \
            else self.select_point_tool
        tool.set_layer(output.layer)

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
        point = self.add_geom(geom, 0, geom_typ='point')
        point.bezeichnung = 'unbenannte Maßnahme'
        point.save()
        self.fill_points_combo(select=point)

    def remove_point(self):
        point = self.parent.ui.points_combo.currentData()
        if not point:
            return
        point.delete()
        self.fill_points_combo()

    def point_selected(self, feature):
        if not self.output_points.layer:
            return
        self.output_points.layer.removeSelection()
        self.output_points.layer.select(feature.id())
        fid = feature.id()
        for idx in range(len(self.parent.ui.points_combo)):
            if fid == self.parent.ui.points_combo.itemData(idx).id:
                break
        self.parent.ui.points_combo.setCurrentIndex(idx)

    def toggle_point(self, point=None):
        if not point:
            point = self.parent.ui.points_combo.currentData()
        self.setup_point_params(point)
        if not point:
            return
        if self.output_points.layer:
            self.output_points.layer.removeSelection()
            self.output_points.layer.select(point.id)
        self.setup_point_params(point)

    def setup_point_params(self, point):
        layout = self.parent.ui.point_parameter_group.layout()
        clearLayout(layout)
        if not point:
            return
        self.params = Params(
            layout, help_file='infrastruktur_punktmassnahme.txt')
        self.params.bezeichnung = Param(point.bezeichnung, LineEdit(width=300),
                                        label='Bezeichnung')


        punktelemente = list(self.parent.netzelemente.filter(Typ='Punkt'))
        type_names = [p.Netzelement for p in punktelemente]
        typ = self.parent.netzelemente.get(IDNetzelement=point.IDNetzelement)

        type_combo = ComboBox(type_names, data=list(punktelemente), width=300)

        self.params.typ = Param(
            typ.Netzelement if typ else 'nicht gesetzt',
            type_combo,
            label='Netzelement'
        )

        self.params.add(Seperator(margin=0))

        self.params.lebensdauer = Param(
            point.lebensdauer, SpinBox(maximum=1000),
            label='Lebensdauer'
        )
        self.params.euro_EH = Param(
            point.euro_EH, DoubleSpinBox(),
            unit='€', label='Euro EH'
        )
        self.params.euro_EN = Param(
            point.euro_EN, DoubleSpinBox(),
            unit='€', label='Euro EN'
        )
        self.params.cent_BU = Param(
            point.cent_BU, DoubleSpinBox(),
            unit='€', label='Cent BU'
        )

        def save():
            point.bezeichnung = self.params.bezeichnung.value
            typ = type_combo.get_data()
            point.IDNetzelement = typ.IDNetzelement
            point.lebensdauer = self.params.lebensdauer.value
            point.euro_EH = self.params.euro_EH.value
            point.euro_EN = self.params.euro_EN.value
            point.cent_BU = self.params.cent_BU.value
            point.save()
            # lazy way to update the combo box
            self.fill_points_combo(select=point)

        self.params.show()
        self.params.changed.connect(save)


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
        self.netzelemente = self.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten'
        ).features()
        self.drawing.load_content()
