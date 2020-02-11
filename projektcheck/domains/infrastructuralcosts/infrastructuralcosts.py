from qgis.PyQt.Qt import QRadioButton

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

from .diagrams import (GesamtkostenDiagramm, KostentraegerDiagramm,
                       NetzlaengenDiagramm)
from .calculations import (GesamtkostenErmitteln, KostentraegerAuswerten,
                           apply_kostenkennwerte)
from .tables import (ErschliessungsnetzLinien, ErschliessungsnetzPunkte,
                     Kostenaufteilung, KostenkennwerteLinienelemente)


class InfrastructureDrawing:
    layer_group = 'Wirkungsbereich 6 - Infrastrukturfolgekosten'

    def __init__(self, ui, project, canvas):
        self.ui = ui
        self.project = project
        self.canvas = canvas
        self.ui.show_lines_button.clicked.connect(
            lambda: self.draw_output('line'))
        self.ui.show_lines_button.setCheckable(False)
        self.ui.show_points_button.clicked.connect(
            lambda: self.draw_output('point'))
        self.ui.show_points_button.setCheckable(False)

        self.ui.points_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_point(
                self.ui.points_combo.currentData()))
        self.ui.infrastrukturmengen_button.clicked.connect(
            self.infrastrukturmengen)

        self.ui.remove_point_button.clicked.connect(self.remove_point)

        self.setup_tools()

    def load_content(self):
        self.netzelemente = self.project.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten'
        ).features()
        self.lines = ErschliessungsnetzLinien.features(create=True)
        self.points = ErschliessungsnetzPunkte.features(create=True)
        self.output_lines = ProjectLayer.from_table(
            self.lines.table, groupname=self.layer_group,
            prepend=True)
        self.output_points = ProjectLayer.from_table(
            self.points.table, groupname=self.layer_group,
            prepend=True)
        self.fill_points_combo()

    def fill_points_combo(self, select=None):
        self.ui.points_combo.blockSignals(True)
        self.ui.points_combo.clear()
        points = [point for point in self.points]
        points.sort(key=lambda x: x.IDNetzelement)
        self.ui.points_combo.addItem('nichts ausgewählt')
        idx = 0
        for i, point in enumerate(points):
            typ = self.netzelemente.get(IDNetzelement=point.IDNetzelement)
            self.ui.points_combo.addItem(
                f'{point.bezeichnung} ({typ.Netzelement if typ else "-"})',
                point
            )
            if select and point.id == select.id:
                idx = i + 1
        if idx:
            self.ui.points_combo.setCurrentIndex(idx)
        self.ui.points_combo.blockSignals(False)
        self.toggle_point()

    def setup_tools(self):
        self.line_tools = {
            self.ui.anliegerstrasse_innere_button: 11,
            self.ui.sammelstrasse_innere_button: 12,
            self.ui.anliegerstrasse_aeussere_button: 21,
            self.ui.sammelstrasse_aeussere_button: 22,
            self.ui.kanal_trennsystem_button: 31,
            self.ui.kanal_mischsystem_button: 32,
            self.ui.kanal_schmutzwasser_button: 33,
            self.ui.trinkwasserleitung_button: 41,
            self.ui.stromleitung_button: 51
        }

        for button, net_id in self.line_tools.items():
            button.clicked.connect(lambda: self.draw_output('line'))
            tool = LineMapTool(button, canvas=self.canvas)
            tool.drawn.connect(
                lambda geom, i=net_id: self.add_geom(geom, i, geom_typ='line'))

        self.select_lines_tool = FeaturePicker(
            self.ui.select_lines_button, canvas=self.canvas)
        self.ui.select_lines_button.clicked.connect(
            lambda: self.draw_output('line'))
        self.select_lines_tool.feature_picked.connect(self.line_selected)
        self.ui.remove_lines_button.clicked.connect(
            self.remove_selected_lines)

        self.draw_point_tool = MapClickedTool(
            self.ui.add_point_button, canvas=self.canvas)
        self.draw_point_tool.map_clicked.connect(self.add_point)
        self.select_point_tool = FeaturePicker(
            self.ui.select_point_button, canvas=self.canvas)
        self.select_point_tool.feature_picked.connect(self.point_selected)
        self.ui.select_point_button.clicked.connect(
            lambda: self.draw_output('point'))
        self.ui.add_point_button.clicked.connect(
            lambda: self.draw_output('point'))

    def add_geom(self, geom, net_id, geom_typ='line'):
        features = self.lines if geom_typ == 'line' \
            else self.points
        typ = self.netzelemente.get(IDNetzelement=net_id)
        feature = features.add(IDNetzelement=net_id,
                               IDNetz=typ.IDNetz if typ else 0,
                               geom=geom)
        if geom_typ == 'line':
            feature.length = geom.length()
            feature.save()
        if len(features) == 1:
            self.draw_output(geom_typ, redraw=True)
        self.canvas.refreshAllLayers()
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
            feat = self.lines.get(id=qf.id())
            feat.delete()
        self.canvas.refreshAllLayers()

    def add_point(self, geom):
        point = self.add_geom(geom, 0, geom_typ='point')
        point.bezeichnung = 'unbenannte Maßnahme'
        point.save()
        self.fill_points_combo(select=point)

    def remove_point(self):
        point = self.ui.points_combo.currentData()
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
        for idx in range(len(self.ui.points_combo)):
            point = self.ui.points_combo.itemData(idx)
            if point and fid == point.id:
                break
        self.ui.points_combo.setCurrentIndex(idx)

    def toggle_point(self, point=None):
        if self.output_points.layer:
            self.output_points.layer.removeSelection()
        if not point:
            point = self.ui.points_combo.currentData()
        self.setup_point_params(point)
        if not point:
            self.ui.remove_point_button.setVisible(False)
            return
        self.ui.remove_point_button.setVisible(True)
        self.draw_output('point')
        self.output_points.layer.select(point.id)
        self.setup_point_params(point)

    def setup_point_params(self, point):
        ui_group = self.ui.point_parameter_group
        layout = ui_group.layout()
        clearLayout(layout)
        if not point:
            return
        self.params = Params(
            layout, help_file='infrastruktur_punktmassnahme.txt')
        self.params.bezeichnung = Param(point.bezeichnung, LineEdit(width=300),
                                        label='Bezeichnung')


        punktelemente = list(self.netzelemente.filter(Typ='Punkt'))
        type_names = [p.Netzelement for p in punktelemente]
        typ = self.netzelemente.get(IDNetzelement=point.IDNetzelement)

        type_combo = ComboBox(type_names, data=list(punktelemente), width=300)

        self.params.typ = Param(
            typ.Netzelement if typ else 'nicht gesetzt',
            type_combo,
            label='Erschließungsnetz'
        )

        self.params.add(Seperator(margin=0))

        self.params.lebensdauer = Param(
            point.Lebensdauer, SpinBox(maximum=1000),
            label='Technische oder wirtschaftliche \n'
            'Lebensdauer bis zur Erneuerung',
            unit='Jahr(e)'
        )
        self.params.euro_EH = Param(
            point.Euro_EH, DoubleSpinBox(),
            unit='€', label='Kosten der erstmaligen Herstellung'
        )
        self.params.euro_EN = Param(
            point.Euro_EN, DoubleSpinBox(),
            unit='€', label='Erneuerungskosten nach Ablauf der Lebensdauer'
        )
        self.params.euro_BU = Param(
            point.Cent_BU / 100, DoubleSpinBox(),
            unit='€', label='Jährliche Kosten für Betrieb und Unterhaltung'
        )

        def save():
            point.bezeichnung = self.params.bezeichnung.value
            typ = type_combo.get_data()
            point.IDNetzelement = typ.IDNetzelement
            point.IDNet = typ.IDNetz
            point.Lebensdauer = self.params.lebensdauer.value
            point.Euro_EH = self.params.euro_EH.value
            point.Euro_EN = self.params.euro_EN.value
            point.Cent_BU = self.params.euro_BU.value * 100
            point.save()
            # lazy way to update the combo box
            self.fill_points_combo(select=point)

        self.params.show()
        self.params.changed.connect(save)

    def infrastrukturmengen(self):
        diagram = NetzlaengenDiagramm(project=self.project)
        diagram.draw()


class Gesamtkosten:

    def __init__(self, ui, project):
        self.ui = ui
        self.project = project
        self.ui.gesamtkosten_button.clicked.connect(self.calculate_gesamtkosten)

        self.ui.kostenkennwerte_widget.setVisible(False)
        self.netzelemente = self.project.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten'
        ).features().filter(Typ='Linie')

        for i, netzelement in enumerate(self.netzelemente):
            net_element_id = netzelement.IDNetzelement
            radio = QRadioButton(netzelement.Netzelement)
            self.ui.kostenkennwerte_radio_grid.addWidget(radio, i // 2, i % 2)
            if i == 0:
                self.net_element_id = net_element_id
                radio.setChecked(True)
            radio.toggled.connect(
                lambda b, i=net_element_id: self.setup_net_element(i)
            )

    def load_content(self):
        self.kostenkennwerte = KostenkennwerteLinienelemente.features(
            create=True)
        if len(self.kostenkennwerte) == 0:
            apply_kostenkennwerte(self.project)
        self.setup_net_element(self.net_element_id)

    def calculate_gesamtkosten(self):
        job = GesamtkostenErmitteln(self.project)

        def on_close(success):
            diagram = GesamtkostenDiagramm(project=self.project,
                                           years=GesamtkostenErmitteln.years)
            diagram.draw()

        dialog = ProgressDialog(job, parent=self.ui, on_close=on_close)
        dialog.show()

    def setup_net_element(self, net_element_id):
        self.net_element_id = net_element_id
        ui_group = self.ui.kostenkennwerte_params_group
        net_element_name = self.netzelemente.get(
            IDNetzelement=net_element_id).Netzelement
        ui_group.setTitle(net_element_name)
        layout = ui_group.layout()
        clearLayout(layout)
        net_element = self.kostenkennwerte.get(IDNetzelement=net_element_id)

        self.params = Params(
            layout, help_file='infrastruktur_kostenkennwerte.txt')

        self.params.lebensdauer = Param(
            net_element.Lebensdauer, SpinBox(maximum=1000),
            label='Lebensdauer: Jahre zwischen den Erneuerungszyklen',
            unit='Jahr(e)'
        )
        self.params.euro_EH = Param(
            net_element.Euro_EH, DoubleSpinBox(),
            unit='€', label='Kosten der erstmaligen Herstellung: \n'
            'Euro pro laufenen Meter'
        )
        self.params.euro_EN = Param(
            net_element.Euro_EN, DoubleSpinBox(),
            unit='€', label='Kosten der Erneuerung: \n'
            'Euro pro laufenden Meter und Erneuerungszyklus'
        )
        self.params.cent_BU = Param(
            net_element.Cent_BU, SpinBox(),
            unit='ct', label='Jährliche Kosten für Betrieb und Unterhaltung: \n'
            'Cent pro laufenden Meter und Jahr'
        )

        self.params.show()
        self.params.changed.connect(lambda: self.save(net_element_id))


    def save(self, net_element_id):
        net_element = self.kostenkennwerte.get(IDNetzelement=net_element_id)
        net_element.Euro_EH = self.params.euro_EH.value
        net_element.Lebensdauer = self.params.lebensdauer.value
        net_element.Cent_BU = self.params.cent_BU.value
        net_element.Euro_EN = self.params.euro_EN.value
        net_element.save()


class Kostentraeger:

    def __init__(self, ui, project):
        self.ui = ui
        self.project = project
        self.ui.kostentraeger_button.clicked.connect(
            self.calculate_kostentraeger)
        self.ui.kostenaufteilung_widget.setVisible(False)

        self.default_kostenaufteilung = self.project.basedata.get_table(
            'Kostenaufteilung_Startwerte', 'Kosten')
        self.kostenphasen = self.project.basedata.get_table(
            'Kostenphasen', 'Kosten').features()
        self.aufteilungsregeln = self.project.basedata.get_table(
            'Aufteilungsregeln', 'Kosten').features()
        self.applyable_aufteilungsregeln = self.project.basedata.get_table(
            'Aufteilungsregeln_zu_Netzen_und_Phasen', 'Kosten').features()
        self.netzelemente = self.project.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten', fields=['IDNetz', 'Netz']
        ).features()

        df_netzelemente = self.netzelemente.to_pandas()
        del df_netzelemente['fid']
        df_netzelemente.drop_duplicates(inplace=True)


        for i, (index, row) in enumerate(df_netzelemente.iterrows()):
            net_id = row['IDNetz']
            net_name = row['Netz']
            radio = QRadioButton(net_name)
            self.ui.kostenaufteilung_radio_grid.addWidget(radio, i // 2, i % 2)
            if i == 0:
                self.net_id = net_id
                radio.setChecked(True)
            radio.toggled.connect(
                lambda b, i=net_id: self.setup_kostenaufteilung(i))

    def load_content(self):
        self.kostenaufteilung = Kostenaufteilung.features(
            create=True, project=self.project)

        # initialize empty project 'kostenaufteilungen' with the default ones
        if len(self.kostenaufteilung) == 0:
            self.kostenaufteilung.update_pandas(
                self.default_kostenaufteilung.to_pandas())

        self.setup_kostenaufteilung(self.net_id)

    def calculate_kostentraeger(self):
        job = KostentraegerAuswerten(self.project)

        def on_close(success):
            # the years originate from gesamtkosten calculation
            diagram = KostentraegerDiagramm(project=self.project,
                                           years=GesamtkostenErmitteln.years)
            diagram.draw()

        dialog = ProgressDialog(job, parent=self.ui,  on_close=on_close)
        dialog.show()

    def setup_kostenaufteilung(self, net_id):
        self.net_id = net_id
        ui_group = self.ui.kostenaufteilung_params_group
        net_name = self.netzelemente.filter(IDNetz=net_id)[0].Netz
        ui_group.setTitle(net_name)
        layout = ui_group.layout()
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
            param = Param(0, preset_combo, label='Vorschlagswerte')
            param.hide_in_overview = True
            self.params.add(param, name=f'{phase.Kostenphase}_presets')

            for j, field_name in enumerate(field_names):
                label = labels[j]
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
            [None] + rules
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

    def setupUi(self):
        self.drawing = InfrastructureDrawing(self.ui, project=self.project,
                                             canvas=self.canvas)
        self.kostenaufteilung = Kostentraeger(self.ui, project=self.project)
        self.gesamtkosten = Gesamtkosten(self.ui, project=self.project)

    def load_content(self):
        self.drawing.load_content()
        self.kostenaufteilung.load_content()
        self.gesamtkosten.load_content()


