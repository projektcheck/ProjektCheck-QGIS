from qgis.PyQt.Qt import QRadioButton, QPushButton
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox
import numpy as np
import os

from projektchecktools.base.domain import Domain
from projektchecktools.base.tools import LineMapTool
from projektchecktools.base.project import ProjectLayer
from projektchecktools.base.tools import FeaturePicker, MapClickedTool
from projektchecktools.utils.utils import clear_layout
from projektchecktools.base.params import (Params, Param, Title, Seperator,
                                           SumDependency)
from projektchecktools.base.inputs import (SpinBox, ComboBox, LineEdit,
                                           Slider, DoubleSpinBox)
from projektchecktools.base.dialogs import ProgressDialog

from .diagrams import (GesamtkostenDiagramm, KostentraegerDiagramm,
                       NetzlaengenDiagramm, VergleichWEDiagramm,
                       VergleichAPDiagramm, MassnahmenKostenDiagramm)
from .calculations import (GesamtkostenErmitteln, KostentraegerAuswerten,
                           apply_kostenkennwerte)
from .tables import (ErschliessungsnetzLinienZeichnung,
                     ErschliessungsnetzPunkte, ErschliessungsnetzLinien,
                     Kostenaufteilung, KostenkennwerteLinienelemente)
from projektchecktools.domains.definitions.tables import Teilflaechen
from projektchecktools.domains.constants import Nutzungsart
from projektchecktools.utils.utils import open_file


class InfrastructureDrawing:

    def __init__(self, ui, project, canvas, layer_group):
        self.ui = ui
        self.layer_group = layer_group
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

        self.setup_tools()

        self.point_params = None
        self.line_params = None

    def load_content(self):
        self.netzelemente = self.project.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten'
        ).features()
        self.drawn_lines = ErschliessungsnetzLinienZeichnung.features(
            create=True)
        self.line_elements = ErschliessungsnetzLinien.features(
            create=True)
        self.points = ErschliessungsnetzPunkte.features(create=True)
        self.output_lines = ProjectLayer.from_table(
            self.drawn_lines.table, groupname=self.layer_group,
            prepend=True)
        self.output_points = ProjectLayer.from_table(
            self.points.table, groupname=self.layer_group,
            prepend=True)
        self.fill_points_combo()
        self.setup_line_params()

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
        self._tools = []
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
            self._tools.append(tool)

        self.select_lines_tool = FeaturePicker(
            self.ui.select_lines_button, canvas=self.canvas)
        self.ui.select_lines_button.clicked.connect(
            lambda: self.draw_output('line'))
        self.select_lines_tool.feature_picked.connect(self.line_selected)
        self.ui.remove_lines_button.clicked.connect(
            self.remove_selected_lines)
        self.ui.remove_drawing_button.clicked.connect(
            self.remove_drawing)
        self._tools.append(self.select_lines_tool)

        self.draw_point_tool = MapClickedTool(
            self.ui.add_point_button, canvas=self.canvas,
            target_epsg=self.project.settings.EPSG)
        self.draw_point_tool.map_clicked.connect(self.add_point)
        self.select_point_tool = FeaturePicker(
            self.ui.select_point_button, canvas=self.canvas)
        self.select_point_tool.feature_picked.connect(self.point_selected)
        self.ui.select_point_button.clicked.connect(
            lambda: self.draw_output('point'))
        self.ui.add_point_button.clicked.connect(
            lambda: self.draw_output('point'))
        self._tools.append(self.draw_point_tool)

    def add_geom(self, geom, net_id, geom_typ='line'):
        features = self.drawn_lines if geom_typ == 'line' \
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
        if not layer:
            return
        for qf in layer.selectedFeatures():
            feat = self.drawn_lines.get(id=qf.id())
            if feat:
                feat.delete()
        self.canvas.refreshAllLayers()

    def remove_drawing(self):
        reply = QMessageBox.question(
            self.ui, 'Zeichnung löschen',
            f'Sollen alle gezeichneten Linienelemente gelöscht werden?',
            QMessageBox.Yes, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        self.drawn_lines.delete()
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
        reply = QMessageBox.question(
            self.ui, 'Maßnahme entfernen',
            f'Soll die punktuelle Maßnahme "{point.bezeichnung}" '
            'entfernt werden?\n',
             QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
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
            self.ui.point_parameter_group.setVisible(False)
            return
        self.ui.point_parameter_group.setVisible(True)
        self.draw_output('point')
        self.output_points.layer.select(point.id)
        self.setup_point_params(point)

    def setup_point_params(self, point):
        if self.point_params:
            self.point_params.close()
        ui_group = self.ui.point_parameter_group
        layout = ui_group.layout()
        clear_layout(layout)
        if not point:
            return
        self.point_params = Params(
            layout, help_file='infrastruktur_punktmassnahme.txt')
        self.point_params.bezeichnung = Param(
            point.bezeichnung, LineEdit(width=300),
            label='Bezeichnung')

        punktelemente = list(self.netzelemente.filter(Typ='Punkt'))
        type_names = [p.Netzelement for p in punktelemente]
        typ = self.netzelemente.get(IDNetzelement=point.IDNetzelement)

        type_combo = ComboBox( ['nicht gesetzt'] + type_names,
                               data=[None] + list(punktelemente), width=300)

        self.point_params.typ = Param(
            typ.Netzelement if typ else 'nicht gesetzt', type_combo,
            label='Erschließungsnetz'
        )

        self.point_params.add(Seperator(margin=0))

        self.point_params.euro_EH = Param(
            point.Euro_EH, DoubleSpinBox(),
            unit='€', label='Kosten der erstmaligen Herstellung'
        )

        self.point_params.euro_BU = Param(
            point.Cent_BU / 100, DoubleSpinBox(),
            unit='€', label='Jährliche Kosten für Betrieb und Unterhaltung'
        )
        self.point_params.euro_EN = Param(
            point.Euro_EN, DoubleSpinBox(),
            unit='€', label='Erneuerungskosten nach Ablauf der Lebensdauer'
        )
        self.point_params.lebensdauer = Param(
            point.Lebensdauer, SpinBox(minimum=1, maximum=1000),
            label='Technische oder wirtschaftliche \n'
            'Lebensdauer bis zur Erneuerung',
            unit='Jahr(e)'
        )

        def save():
            point.bezeichnung = self.point_params.bezeichnung.value
            typ = type_combo.get_data()
            point.IDNetzelement = typ.IDNetzelement if typ else 0
            point.IDNetz = typ.IDNetz if typ else 0
            point.Lebensdauer = self.point_params.lebensdauer.value
            point.Euro_EH = self.point_params.euro_EH.value
            point.Euro_EN = self.point_params.euro_EN.value
            point.Cent_BU = self.point_params.euro_BU.value * 100
            point.save()
            # lazy way to update the combo box
            self.fill_points_combo(select=point)

        self.point_params.show()
        self.point_params.changed.connect(save)

        last_row = self.point_params.layout.children()[-1]
        button = QPushButton()
        icon_path = 'iconset_mob/20190619_iconset_mob_delete_1.png'
        icon = QIcon(os.path.join(self.project.settings.IMAGE_PATH, icon_path))
        button.setText('Maßnahme entfernen')
        button.setIcon(icon)
        button.setToolTip(
            '<p><span style=" font-weight:600;">Maßnahme entfernen</span>'
            '</p><p>Löscht die aktuell gewählte Maßnahme. '
            '<br/>Dieser Schritt kann nicht rückgängig gemacht werden. </p>')
        last_row.insertWidget(0, button)
        button.clicked.connect(self.remove_point)

    def init_lines(self):
        line_elements = self.netzelemente.filter(Typ='Linie')
        df_line_elements = line_elements.to_pandas()
        del(df_line_elements['fid'])
        self.line_elements.update_pandas(df_line_elements)
        # reset filter ToDo: fix filtering
        self.netzelemente.filter()

    def setup_line_params(self):
        layout = self.ui.mengen_params_group.layout()
        clear_layout(layout)
        if len(self.line_elements) == 0:
            self.init_lines()
        self.line_params = Params(
            layout, help_file='infrastruktur_linienelemente.txt')
        for element in self.line_elements:
            param = Param(int(element.length), Slider(maximum=10000),
                          label=element.Netzelement, unit='m')
            self.line_params.add(
                param, name=f'netzelement_{element.IDNetzelement}')

        def save():
            for element in self.line_elements:
                param = self.line_params[f'netzelement_{element.IDNetzelement}']
                element.length = param.value
                element.save()

        self.line_params.show(title=self.ui.mengen_params_group.title())
        self.line_params.changed.connect(save)

        last_row = self.line_params.layout.children()[-1]
        button = QPushButton()
        button.setText('aus Zeichnung übernehmen')
        last_row.insertWidget(0, button)
        button.clicked.connect(self.apply_drawing)

    def apply_drawing(self):
        df_drawing = self.drawn_lines.to_pandas()
        for element in self.line_elements:
            param = self.line_params[f'netzelement_{element.IDNetzelement}']
            drawn_elements = df_drawing[
                df_drawing['IDNetzelement']==element.IDNetzelement]
            length = int(drawn_elements['length'].sum())
            param.value = length
            element.length = length
            element.save()

    def infrastrukturmengen(self):
        diagram = NetzlaengenDiagramm(project=self.project)
        diagram.draw()

        diagram = MassnahmenKostenDiagramm(project=self.project)
        diagram.draw(offset_x=100, offset_y=100)

    def close(self):
        for tool in self._tools:
            tool.set_active(False)
        if self.point_params:
            self.point_params.close()
        if self.line_params:
            self.line_params.close()


class Gesamtkosten:

    def __init__(self, ui, project):
        self.ui = ui
        self.project = project
        self.ui.gesamtkosten_button.clicked.connect(self.calculate_gesamtkosten)

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

        def on_close():
            if not self.dialog.success:
                return
            diagram = GesamtkostenDiagramm(project=self.project,
                                           years=GesamtkostenErmitteln.years)
            diagram.draw()

        self.dialog = ProgressDialog(job, parent=self.ui, on_close=on_close,
                                     auto_close=True)
        self.dialog.show()

    def setup_net_element(self, net_element_id):
        self.net_element_id = net_element_id
        ui_group = self.ui.kostenkennwerte_params_group
        net_element_name = self.netzelemente.get(
            IDNetzelement=net_element_id).Netzelement
        ui_group.setTitle(net_element_name)
        layout = ui_group.layout()
        clear_layout(layout)
        net_element = self.kostenkennwerte.get(IDNetzelement=net_element_id)

        self.params = Params(
            layout, help_file='infrastruktur_kostenkennwerte.txt')

        self.params.euro_EH = Param(
            net_element.Euro_EH, DoubleSpinBox(),
            unit='€', label='Kosten der erstmaligen Herstellung \n'
            'pro laufenden Meter'
        )
        self.params.euro_BU = Param(
            net_element.Cent_BU / 100, DoubleSpinBox(),
            unit='€', label='Jährliche Kosten für Betrieb und Unterhaltung \n'
            'pro laufenden Meter und Jahr'
        )
        self.params.euro_EN = Param(
            net_element.Euro_EN, DoubleSpinBox(),
            unit='€', label='Kosten der Erneuerung \n'
            'pro laufenden Meter und Erneuerungszyklus'
        )
        self.params.lebensdauer = Param(
            net_element.Lebensdauer, SpinBox(minimum=1, maximum=1000),
            label='Lebensdauer: Jahre zwischen den Erneuerungszyklen',
            unit='Jahr(e)'
        )

        self.params.show()
        self.params.changed.connect(lambda: self.save(net_element_id))


    def save(self, net_element_id):
        net_element = self.kostenkennwerte.get(IDNetzelement=net_element_id)
        net_element.Euro_EH = self.params.euro_EH.value
        net_element.Lebensdauer = self.params.lebensdauer.value
        net_element.Cent_BU = self.params.euro_BU.value * 100
        net_element.Euro_EN = self.params.euro_EN.value
        net_element.save()


class Kostentraeger:

    def __init__(self, ui, project):
        self.ui = ui
        self.project = project
        self.ui.kostentraeger_button.clicked.connect(
            self.calculate_kostentraeger)

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
            for default in self.default_kostenaufteilung.features():
                rule =self.aufteilungsregeln.get(
                    IDAufteilungsregel=default.IDKostenregel)
                self.kostenaufteilung.add(
                    Anteil_GSB=rule.Anteil_GSB,
                    Anteil_GEM=rule.Anteil_GEM,
                    Anteil_ALL=rule.Anteil_ALL,
                    IDNetz=default.IDNetz,
                    IDKostenphase=default.IDKostenphase
                )

        self.setup_kostenaufteilung(self.net_id)

    def calculate_kostentraeger(self):
        job = KostentraegerAuswerten(self.project)

        def on_close():
            if not self.dialog.success:
                return
            # the years originate from gesamtkosten calculation
            diagram = KostentraegerDiagramm(project=self.project,
                                           years=GesamtkostenErmitteln.years)
            diagram.draw()

        self.dialog = ProgressDialog(job, parent=self.ui,  on_close=on_close,
                                     auto_close=True)
        self.dialog.show()

    def setup_kostenaufteilung(self, net_id):
        self.net_id = net_id
        ui_group = self.ui.kostenaufteilung_params_group
        net_name = self.netzelemente.filter(IDNetz=net_id)[0].Netz
        ui_group.setTitle(net_name)
        layout = ui_group.layout()
        clear_layout(layout)

        self.params = Params(
            layout, help_file='infrastruktur_kostenaufteilung.txt')
        field_names = ['Anteil_GSB', 'Anteil_GEM', 'Anteil_ALL']
        labels = ['Kostenanteil der Grunstücksbesitzer/innen',
                  'Kostenanteil der Gemeinde',
                  'Netznutzer/innen und Tarifkundschaft']

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

            preset_combo, options = self.create_presets(
                net_id, phase.IDKostenphase)
            param = Param(0, preset_combo, label='Vorschlagswerte')
            param.hide_in_overview = True
            self.params.add(param, name=f'{phase.Kostenphase}_presets')

            for j, field_name in enumerate(field_names):
                label = labels[j]
                slider = Slider(maximum=100, lockable=True)
                param = Param(feature[field_name], slider,
                              label=label, unit='%')
                self.params.add(
                    param, name=f'{phase.Kostenphase}_{field_name}')
                dependency.add(param)
                slider.changed.connect(
                    lambda b,
                    c=preset_combo, o=options: c.set_value(o[0]))

            if i != len(self.kostenphasen) - 1:
                self.params.add(Seperator(margin=0))

            preset_combo.changed.connect(
                lambda b, c=preset_combo, p=phase: preset_changed(c, p))

        self.params.show(title='Kostenaufteilung festlegen')
        self.params.changed.connect(lambda: self.save(net_id))

    def create_presets(self, net_id, phase_id):
        applyable_rules = self.applyable_aufteilungsregeln.filter(
            IDNetz=net_id, IDPhase=phase_id)
        rules = []
        for applyable_rule in applyable_rules:
            rule_id = applyable_rule.IDAufteilungsregel
            rule = self.aufteilungsregeln.get(IDAufteilungsregel=rule_id)
            rules.append(rule)

        options = (['Aufteilungsregel wählen'] +
                   [rule.Aufteilungsregel for rule in rules])
        preset_combo = ComboBox(options, [None] + rules)
        preset_combo.input.model().item(0).setEnabled(False)
        return preset_combo, options

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
    ui_icon = ('images/iconset_mob/'
               '20190619_iconset_mob_domain_infrstucturalcosts_4.png')
    layer_group = 'Wirkungsbereich 5 - Infrastrukturfolgekosten'

    def setupUi(self):
        self.drawing = InfrastructureDrawing(self.ui, project=self.project,
                                             canvas=self.canvas,
                                             layer_group=self.layer_group)
        self.kostenaufteilung = Kostentraeger(self.ui, project=self.project)
        self.gesamtkosten = Gesamtkosten(self.ui, project=self.project)
        self.ui.kostenvergleich_button.clicked.connect(self.kostenvergleich)

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Infrastrukturfolgekosten.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

        # quite dumb, but expanding a groupbox sets all children to visible
        # but we don't want to see the collapsed widgets
        def hide_widgets():
            self.ui.kostenaufteilung_button.setChecked(False)
            self.ui.kostenkennwerte_button.setChecked(False)
            self.ui.kostenaufteilung_widget.setVisible(False)
            self.ui.kostenkennwerte_widget.setVisible(False)
        self.ui.evaluation_groupbox.collapsedStateChanged.connect(
            hide_widgets)
        hide_widgets()

    def load_content(self):
        super().load_content()
        self.areas = Teilflaechen.features()
        self.drawing.load_content()
        self.kostenaufteilung.load_content()
        self.gesamtkosten.load_content()

    def kostenvergleich(self):
        types_of_use = [area.nutzungsart for area in self.areas
                        if area.nutzungsart != Nutzungsart.UNDEFINIERT.value]
        if len(np.unique(types_of_use)) != 1:
            QMessageBox.warning(
                self.ui, 'Hinweis', 'Die Funktion steht nur für Projekte zur '
                'Verfügung, bei denen alle Teilflächen '
                'ausschließlich die Nutzung Wohnen bzw. Gewerbe haben.'
            )
            return

        job = GesamtkostenErmitteln(self.project)

        def on_close():
            if not self.dialog.success:
                return
            if types_of_use[0] == Nutzungsart.WOHNEN.value:
                diagram = VergleichWEDiagramm(project=self.project)
            else:
                diagram = VergleichAPDiagramm(project=self.project)
            diagram.draw()

        self.dialog = ProgressDialog(job, parent=self.ui, on_close=on_close,
                                     auto_close=True)
        self.dialog.show()


    def close(self):
        if hasattr(self.kostenaufteilung, 'params'):
            self.kostenaufteilung.params.close()
        if hasattr(self.gesamtkosten, 'params'):
            self.gesamtkosten.params.close()
        self.drawing.close()
        super().close()
