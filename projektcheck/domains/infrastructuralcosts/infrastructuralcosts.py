from projektcheck.base.domain import Domain
from projektcheck.base.tools import LineMapTool
from projektcheck.base.project import ProjectLayer
from projektcheck.base.tools import FeaturePicker, MapClickedTool
from projektcheck.utils.utils import clearLayout
from projektcheck.base.params import (Params, Param, Title, Seperator,
                                      SumDependency)
from projektcheck.base.inputs import (SpinBox, ComboBox, LineEdit,
                                      Slider, DoubleSpinBox)
from projektcheck.base.dialogs import ProgressDialog

from .diagrams import GesamtkostenDiagramm, KostentraegerDiagramm
from .calculations import Gesamtkosten, KostentraegerAuswerten
from .tables import (ErschliessungsnetzLinien, ErschliessungsnetzPunkte,
                     Kostenaufteilung)


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
        typ = self.parent.netzelemente.get(IDNetzelement=net_id)
        feature = features.add(IDNetzelement=net_id,
                               IDNetz=typ.IDNetz if typ else 0,
                               geom=geom)
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
            point.Lebensdauer, SpinBox(maximum=1000),
            label='Lebensdauer'
        )
        self.params.euro_EH = Param(
            point.Euro_EH, DoubleSpinBox(),
            unit='€', label='Euro EH'
        )
        self.params.euro_EN = Param(
            point.Euro_EN, DoubleSpinBox(),
            unit='€', label='Euro EN'
        )
        self.params.cent_BU = Param(
            point.Cent_BU, DoubleSpinBox(),
            unit='€', label='Cent BU'
        )

        def save():
            point.bezeichnung = self.params.bezeichnung.value
            typ = type_combo.get_data()
            point.IDNetzelement = typ.IDNetzelement
            point.IDNet = typ.IDNetz
            point.Lebensdauer = self.params.lebensdauer.value
            point.Euro_EH = self.params.euro_EH.value
            point.Euro_EN = self.params.euro_EN.value
            point.Cent_BU = self.params.cent_BU.value
            point.save()
            # lazy way to update the combo box
            self.fill_points_combo(select=point)

        self.params.show()
        self.params.changed.connect(save)


class Kostentraeger:

    def __init__(self, ui, project):
        self.ui = ui
        self.project = project
        self.ui.kostentraeger_button.clicked.connect(
            self.calculate_kostentraeger)
        self.ui.kostenaufteilung_widget.setVisible(False)

        self.net_radios = {
            self.ui.strasse_innere_radio: 1,
            self.ui.strasse_aeussere_radio: 2,
            self.ui.kanalisation_radio: 3,
            self.ui.trinkwasser_radio: 4,
            self.ui.elektrizitaet_radio: 5
        }

        for radio, net_id in self.net_radios.items():
            radio.toggled.connect(
                lambda b, i=net_id: self.setup_kostenaufteilung(net_id=i))

    def load_content(self):
        self.kostenaufteilung = Kostenaufteilung.features(
            create=True, project=self.project)
        self.default_kostenaufteilung = self.project.basedata.get_table(
            'Kostenaufteilung_Startwerte', 'Kosten')
        self.kostenphasen = self.project.basedata.get_table(
            'Kostenphasen', 'Kosten').features()
        self.aufteilungsregeln = self.project.basedata.get_table(
            'Aufteilungsregeln', 'Kosten').features()
        self.applyable_aufteilungsregeln = self.project.basedata.get_table(
            'Aufteilungsregeln_zu_Netzen_und_Phasen', 'Kosten').features()

        # initialize empty project 'kostenaufteilungen' with the default ones
        if len(self.kostenaufteilung) == 0:
            self.kostenaufteilung.update_pandas(
                self.default_kostenaufteilung.to_pandas())
        # load params for first radion (checking it also triggers setup)
        if not self.ui.strasse_innere_radio.isChecked():
            self.ui.strasse_innere_radio.setChecked(True)
        else:
            self.setup_kostenaufteilung()

    def calculate_kostentraeger(self):
        job = KostentraegerAuswerten(self.project)

        def on_close(success):
            # the years originate from gesamtkosten calculation
            diagram = KostentraegerDiagramm(project=self.project,
                                           years=Gesamtkosten.years)
            diagram.draw()

        dialog = ProgressDialog(job, parent=self.ui,  on_close=on_close)
        dialog.show()

    def setup_kostenaufteilung(self, net_id=1):
        layout = self.ui.kostenaufteilung_params_group.layout()
        clearLayout(layout)

        self.params = Params(
            layout, help_file='infrastruktur_kostenaufteilung.txt')
        field_names = ['Anteil_GSB', 'Anteil_GEM', 'Anteil_ALL']
        labels = ['Kostenanteil der Grunstücksbesitzer*Innen',
                  'Kostenanteil der Gemeinde',
                  'Netznutzer*innen und Tarifkundschaft']

        def preset_changed(c, p):
            preset = c.get_data()
            if not preset:
                return
            for field_name in field_names:
                param = self.params.get(f'{p.Kostenphase}_{field_name}')
                param.input.value = preset[field_name]

        for i, phase in enumerate(self.kostenphasen):
            dependency = SumDependency(100)
            self.params.add(Title(phase.Kostenphase))
            feature = self.kostenaufteilung.get(
                IDKostenphase=phase.IDKostenphase, IDNetz=net_id)

            preset_combo = self.create_presets(net_id, phase.IDKostenphase)
            self.params.add(preset_combo, name=f'{phase.Kostenphase}_presets')

            for i, field_name in enumerate(field_names):
                label = labels[i]
                slider = Slider(maximum=100, lockable=True)
                param = Param(feature[field_name], slider, label=label)
                self.params.add(
                    param, name=f'{phase.Kostenphase}_{field_name}')
                dependency.add(param)
                slider.changed.connect(
                    lambda b, c=preset_combo: c.set_value('Benutzerdefiniert'))

            if i != len(self.kostenphasen) - 1:
                self.params.add(Seperator(margin=0))

            preset_combo.changed.connect(
                lambda b, c=preset_combo, p=phase: preset_changed(c, p))

        self.params.show()
        self.params.changed.connect(lambda: self.save(net_id))

    def create_presets(self, net_id, phase_id):
        applyable_rules = self.applyable_aufteilungsregeln.filter(
            IDNetz=net_id, IDPhase=phase_id)
        rules = []
        for applyable_rule in applyable_rules:
            rule_id = applyable_rule.IDAufteilungsregel
            rule = self.aufteilungsregeln.get(IDAufteilungsregel=rule_id)
            rules.append(rule)

        preset_combo = ComboBox(
            ['Benutzerdefiniert'] + [rule.Aufteilungsregel for rule in rules],
            [None] + rules,
            hide_in_overview=True
        )
        return preset_combo

    def save(self, net_id):
        for phase in self.kostenphasen:
            feature = self.kostenaufteilung.get(
                IDKostenphase=phase.IDKostenphase, IDNetz=net_id)
            for field_name in ['Anteil_GSB', 'Anteil_GEM', 'Anteil_ALL']:
                param = self.params[f'{phase.Kostenphase}_{field_name}']
                feature[field_name] = param.value
            feature.save()


class InfrastructuralCosts(Domain):
    """"""

    ui_label = 'Infrastrukturfolgekosten'
    ui_file = 'ProjektCheck_dockwidget_analysis_06-IFK.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_infrstucturalcosts_4.png"

    layer_group = 'Wirkungsbereich 6 - Infrastrukturfolgekosten'

    def setupUi(self):
        self.drawing = InfrastructureDrawing(self)
        self.kostenaufteilung = Kostentraeger(self.ui, project=self.project)
        self.ui.gesamtkosten_button.clicked.connect(self.calculate_gesamtkosten)

    def load_content(self):
        self.lines = ErschliessungsnetzLinien.features(create=True)
        self.points = ErschliessungsnetzPunkte.features(create=True)
        self.netzelemente = self.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten'
        ).features()
        self.drawing.load_content()
        self.kostenaufteilung.load_content()

    def calculate_gesamtkosten(self):
        job = Gesamtkosten(self.project)

        def on_close(success):
            diagram = GesamtkostenDiagramm(project=self.project,
                                           years=Gesamtkosten.years)
            diagram.draw()

        dialog = ProgressDialog(job, parent=self.ui, on_close=on_close)
        dialog.show()
