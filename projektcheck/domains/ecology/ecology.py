from qgis.PyQt.Qt import QPushButton
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QMessageBox, QVBoxLayout,
                                 QTableWidget, QTableWidgetItem)
import numpy as np

from projektcheck.base.domain import Domain
from projektcheck.base.layers import TileLayer
from projektcheck.base.project import ProjectLayer
from projektcheck.base.tools import PolygonMapTool
from projektcheck.domains.ecology.tables import (BodenbedeckungNullfall,
                                                 BodenbedeckungPlanfall,
                                                 BodenbedeckungAnteile)
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.ecology.diagrams import (
    Leistungskennwerte, LeistungskennwerteDelta)
from projektcheck.base.params import (Params, Param, SumDependency)
from projektcheck.base.dialogs import Dialog
from projektcheck.base.inputs import Slider
from projektcheck.utils.utils import clearLayout

from settings import settings


class Ecology(Domain):
    """"""
    MAX_RATING = 20

    ui_label = 'Ökologie'
    ui_file = 'ProjektCheck_dockwidget_analysis_04-Oeko.ui'
    ui_icon = ('images/iconset_mob/'
               '20190619_iconset_mob_nature_conservation_2.png')
    layer_group = 'Wirkungsbereich 4 - Ökologie'

    geoserver = 'https://geoserver.ggr-planung.de/geoserver/projektcheck/wms?'
    ioer = 'https://monitor.ioer.de/cgi-bin/wms?'
    nature_layers = [
        ('Naturschutzgebiete', f'url={geoserver}&layers=nsg_2017'),
        ('Nationalparke', f'url={geoserver}&layers=nlp2019'),
        ('Nationale Naturmonumente', f'url={geoserver}&layers=nnm_2019'),
        ('FFH-Gebiete', f'url={geoserver}&layers=ffh_de_2018'),
        ('RAMSAR-Gebiete', f'url={geoserver}&layers=ramsar2013'),
        ('Vogelschutzgebiete', f'url={geoserver}&layers=spa_de_2018')
    ]
    landscape_layers = [
        ('Landschaftsschutzgebiete', f'url={geoserver}&layers=lsg_2017'),
        ('Biosphärenreservate', f'url={geoserver}&layers=bio2019'),
        ('Naturparke', f'url={geoserver}&layers=naturparke2019')
    ]
    spaces_layers = [
        ('Unzerschnittene Freiräume > 100m²',
        f'url={ioer}MAP=U04RG_wms&layers=U04RG_2014_100m'),
        ('Unzerschnittene Freiräume > 50m²',
        f'url={ioer}MAP=U03RG_wms&layers=U03RG_2014_100m'),
        ('Anteil Freiraumfläche an Gebietsfläche',
        f'url={ioer}MAP=F01RG_wms&layers=F01RG_2018_100m')
    ]

    wood_layers = [
        ('Unzerschnittene Wälder > 50m²',
        f'url={ioer}MAP=U07RG_wms&layers=U07RG_2014_100m'),
        ('Waldgebiete', f'url={ioer}MAP=O06RG_wms&layers=O06RG_2016_100m')
    ]

    def setupUi(self):
        self.setup_layers()
        self.setup_drawing_tools()
        self.ui.paint_tool_frame.setVisible(False)
        self.ui.toggle_drawing_button.clicked.connect(self.add_output)
        self.output_nullfall = None
        self.output_planfall = None

        self.ui.planfall_radio.toggled.connect(self.toggle_planfall_nullfall)
        self.ui.planfall_radio.toggled.connect(self.add_output)
        self.toggle_planfall_nullfall()

        self.ui.remove_drawing_button.clicked.connect(
            lambda: self.clear_drawing(
                planfall=self.ui.planfall_radio.isChecked()))
        self.ui.calculate_rating_button.clicked.connect(self.calculate_rating)
        self.ui.import_nullfall_button.clicked.connect(self.import_nullfall)
        self.ui.apply_type_button.clicked.connect(
            lambda: self.add_geom(
                self.area, self.get_selected_type(),
                planfall=self.ui.planfall_radio.isChecked()))
        self.ui.remove_type_button.clicked.connect(
            lambda: self.remove_type(
                self.get_selected_type(),
                planfall=self.ui.planfall_radio.isChecked()))
        self.ui.analyse_drawing_button.clicked.connect(
            lambda: self.show_drawing_analysis(
                planfall=self.ui.planfall_radio.isChecked()))

    def toggle_planfall_nullfall(self):
        self.planfall = self.ui.planfall_radio.isChecked()
        self.ui.import_nullfall_button.setVisible(self.planfall)
        disabled_out = self.output_nullfall if self.planfall \
            else self.output_planfall
        if disabled_out:
            disabled_out.set_visibility(False)

    def load_content(self):
        areas = Teilflaechen.features()
        self.area = None
        for area in areas:
            if not self.area:
                self.area = area.geom
            else:
                self.area = self.area.combine(area.geom)
        self.boden_nullfall = BodenbedeckungNullfall.features(create=True)
        self.boden_planfall = BodenbedeckungPlanfall.features(create=True)
        self.anteile = BodenbedeckungAnteile.features(create=True)
        self.bb_types = self.basedata.get_table(
            'Bodenbedeckung', 'Flaeche_und_Oekologie'
        )
        self.faktoren = self.basedata.get_table(
            'Faktoren', 'Flaeche_und_Oekologie'
        )

        self.output_nullfall = ProjectLayer.from_table(
            self.boden_nullfall._table, groupname=self.layer_group,
            prepend=True)
        self.output_planfall = ProjectLayer.from_table(
            self.boden_planfall._table, groupname=self.layer_group,
            prepend=True)
        self.setup_params()

    def setup_params(self):

        self.params_nullfall = Params(self.ui.param_nullfall_tab.layout())
        self.params_planfall = Params(self.ui.param_planfall_tab.layout())
        clearLayout(self.ui.param_nullfall_tab.layout())
        clearLayout(self.ui.param_planfall_tab.layout())

        def apply_nf():
            self.apply_drawing(False)
        def apply_pf():
            self.apply_drawing(True)

        for params, prefix in [(self.params_nullfall, 'nullfall'),
                               (self.params_planfall, 'planfall')]:
            planfall = prefix == 'planfall'
            dependency = SumDependency(100)
            for bb_typ in self.bb_types.features():
                bb_id = bb_typ.IDBodenbedeckung
                feature = self.anteile.get(IDBodenbedeckung=bb_id,
                                           planfall=planfall)
                value = feature.anteil if feature else 0
                slider = Slider(maximum=100, width=200, lockable=True)
                param = Param(
                    value, slider, label=bb_typ.name,
                    unit='%'
                )
                dependency.add(param)
                params.add(param, name=f'{prefix}_{bb_id}')
            params.changed.connect(lambda p=prefix: self.save(p))
            params.show()
            last_row = params.layout.children()[-1]
            button = QPushButton()
            button.setText('aus Zeichnung übernehmen')
            last_row.insertWidget(0, button)
            # workaround: lambda with argument didn't seem to work here (weird)
            #button.clicked.connect(lambda p=planfall: self.apply_drawing(p))
            func = apply_pf if planfall else apply_nf
            button.clicked.connect(func)

    def setup_layers(self):

        def add_layer_from_dict(layers, parent_group):
            for name, url in layers:
                self.add_wms_layer( name, url, parent_group=parent_group)

        self.ui.nature_button.setCheckable(False)
        self.ui.nature_button.clicked.connect(
            lambda: add_layer_from_dict(
                self.nature_layers, parent_group='Natur- und Artenschutz')
        )
        self.ui.landscape_button.setCheckable(False)
        self.ui.landscape_button.clicked.connect(
            lambda: add_layer_from_dict(
                self.landscape_layers, parent_group='Landschaftsschutz')
        )
        self.ui.spaces_100_button.setCheckable(False)
        name_s100, url_s100 = self.spaces_layers[0]
        self.ui.spaces_100_button.clicked.connect(
            lambda: self.add_wms_layer(name_s100, url_s100)
        )
        self.ui.spaces_50_button.setCheckable(False)
        name_s50, url_s50 = self.spaces_layers[1]
        self.ui.spaces_50_button.clicked.connect(
            lambda: self.add_wms_layer(name_s50, url_s50)
        )
        self.ui.spaces_button.setCheckable(False)
        name_s, url_s = self.spaces_layers[2]
        self.ui.spaces_button.clicked.connect(
            lambda: self.add_wms_layer(name_s, url_s)
        )
        self.ui.woods_50_button.setCheckable(False)
        name_w50, url_w50 = self.wood_layers[0]
        self.ui.woods_50_button.clicked.connect(
            lambda: self.add_wms_layer(name_w50, url_w50)
        )
        self.ui.woods_button.setCheckable(False)
        name_w, url_w = self.wood_layers[1]
        self.ui.woods_button.clicked.connect(
            lambda: self.add_wms_layer(name_w, url_w)
        )

    def setup_drawing_tools(self):
        self.drawing_tools = {
            self.ui.draw_builtup_button: 1,
            self.ui.draw_water_button: 2,
            self.ui.draw_plates_button: 3,
            self.ui.draw_trees_button: 4,
            self.ui.draw_perennial_button: 5,
            self.ui.draw_meadow_button: 6,
            self.ui.draw_lawn_button: 7,
            self.ui.draw_cover_button: 8,
            self.ui.draw_concrete_button: 9,
            self.ui.draw_field_button: 10,
            self.ui.draw_paving_button: 11
        }

        for button, floor_id in self.drawing_tools.items():
            tool = PolygonMapTool(button, canvas=self.canvas, draw_markers=True,
                                  line_style=Qt.DotLine)
            tool.drawn.connect(
                lambda geom, i=floor_id: self.add_geom(
                    geom, i,
                    in_area_only=self.ui.in_area_only_check.isChecked(),
                    planfall=self.ui.planfall_radio.isChecked()
                ))

    def add_geom(self, geom, typ, unite=True, in_area_only=True,
                 difference=True, planfall=True):
        if geom.isEmpty() or geom.isNull() or typ is None:
            return
        if in_area_only:
            geom = geom.intersection(self.area)
        features = self.boden_planfall if planfall else self.boden_nullfall
        if not unite:
            features.add(geom=geom, IDBodenbedeckung=typ, area=geom.area())
        else:
            ex_feat = features.get(IDBodenbedeckung=typ)
            if not ex_feat:
                features.add(geom=geom, IDBodenbedeckung=typ,
                             area=geom.area())
            else:
                ex_feat.geom = ex_feat.geom.combine(geom)
                ex_feat.area = ex_feat.geom.area()
                ex_feat.save()
        if difference:
            # ToDo: fix filtering, works but messes up previous filtering
            #others = features.filter(IDBodenbedeckung__ne=floor_id)
            for feature in features:
                if feature.IDBodenbedeckung == typ:
                    continue
                difference = feature.geom.difference(geom)
                # ToDo: handle invalid and null geometries instead of ignoring
                if not (difference.isNull() or difference.isEmpty()):
                    feature.geom = difference
                    feature.area = difference.area()
                    feature.save()
        self.canvas.refreshAllLayers()
        # workaround: layer style is not applied correctly
        # with empty features -> redraw on first geometry
        if len(features) == 1:
            self.add_output()

    def remove_type(self, typ, planfall=True):
        if not typ:
            return
        features = self.boden_planfall if planfall else self.boden_nullfall
        # ToDo: filter would be better but messes up original filter atm
        for feature in features:
            if feature.IDBodenbedeckung == typ:
                feature.delete()
        self.canvas.refreshAllLayers()

    def save(self, prefix):
        planfall = prefix == 'planfall'
        params = self.params_planfall if planfall else self.params_nullfall
        for bb_typ in self.bb_types.features():
            bb_id = bb_typ.IDBodenbedeckung
            feature = self.anteile.get(IDBodenbedeckung=bb_id,
                                       planfall=planfall)

            if not feature:
                feature = self.anteile.add(IDBodenbedeckung=bb_id)
                feature.planfall = planfall
            feature.anteil = params.get(f'{prefix}_{bb_id}').value
            feature.save()

    def import_nullfall(self):
        if len(self.boden_planfall) > 0:
            reply = QMessageBox.question(
                self.ui, 'Nullfall in Planfall importieren',
                'Achtung: die existierende Zeichnung für den Planfall '
                'wird beim Import des Nullfalls gelöscht.',
                QMessageBox.Yes, QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
        self.boden_planfall.delete()
        for feature in self.boden_nullfall:
            self.boden_planfall.add(geom=feature.geom,
                                    IDBodenbedeckung=feature.IDBodenbedeckung,
                                    area=feature.geom.area())
        self.canvas.refreshAllLayers()

    def get_selected_type(self):
        for button, typ in self.drawing_tools.items():
            if button.isChecked():
                return typ
        return None

    def analyse_shares(self, planfall=True):
        features = self.boden_planfall if planfall else self.boden_nullfall
        df = features.to_pandas()
        grouped = df.groupby('IDBodenbedeckung')
        grouped_sums = grouped['area'].sum()
        sum_area = df['area'].sum()
        shares = (grouped_sums * 100 / sum_area).round() if sum_area > 0 \
            else grouped_sums
        return shares

    def apply_drawing(self, planfall=True):
        shares = self.analyse_shares(planfall)
        params = self.params_planfall if planfall else self.params_nullfall
        prefix = 'planfall' if planfall else 'nullfall'
        for bb_typ in self.bb_types.features():
            bb_id = bb_typ.IDBodenbedeckung
            params.get(f'{prefix}_{bb_id}').value = shares.get(bb_id) or 0
        self.save(prefix)

    def show_drawing_analysis(self, planfall=True):
        shares = self.analyse_shares(planfall)
        dialog = Dialog(title='Anteile Bodenbedeckung')
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        tableWidget = QTableWidget()
        layout.addWidget(tableWidget)
        tableWidget.setColumnCount(2)
        tableWidget.setHorizontalHeaderItem(
            0, QTableWidgetItem('Bodenbedeckungstyp'))
        tableWidget.setHorizontalHeaderItem(
            1, QTableWidgetItem('Anteil'))
        types = self.bb_types.features()
        tableWidget.setRowCount(len(types))
        for i, bb_typ in enumerate(types):
            share = shares.get(bb_typ.IDBodenbedeckung) or 0
            tableWidget.setItem(i, 0, QTableWidgetItem(bb_typ.name))
            tableWidget.setItem(i, 1, QTableWidgetItem(f'{share}%'))
        dialog.show()

    def clear_drawing(self, planfall=True):
        l = 'Planfall' if planfall else 'Nullfall'
        reply = QMessageBox.question(
            self.ui, 'Zeichnung löschen',
            f'Sollen alle gezeichneten Flächen für den {l} entfernt werden?',
            QMessageBox.Yes, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        features = self.boden_planfall if planfall else self.boden_nullfall
        output = self.output_planfall if self.planfall \
            else self.output_nullfall
        layer = output.layer
        # remove selection, so that qgis is free to remove them from canvas
        layer.removeSelection()
        features.delete()
        self.canvas.refreshAllLayers()

    def add_output(self):
        planfall = self.ui.planfall_radio.isChecked()
        label = 'Bodenbedeckung '
        label += 'Planfall' if planfall else 'Nullfall'
        output = self.output_planfall if planfall else self.output_nullfall
        style = 'flaeche_oekologie_bodenbedeckung_planfall.qml' if planfall \
            else 'flaeche_oekologie_bodenbedeckung_nullfall.qml'
        output.draw(label=label, style_file=style)
        setattr(self, 'output_planfall' if self.planfall else 'output_nullfall',
                output)
        self.toggle_planfall_nullfall()

    def add_wms_layer(self, name, url, parent_group=None):
        group = (f'{self.project.groupname}/{self.layer_group}')
        if parent_group:
            group += f'/{parent_group}'
        url = (f'{url}&crs=EPSG:{settings.EPSG}'
               '&format=image/png&dpiMode=7&styles')
        layer = TileLayer(url, groupname=group)
        layer.draw(name)

    def calculate_rating(self):
        df_factors = self.faktoren.to_pandas()
        df_shares = self.anteile.to_pandas()
        df_merged = df_shares.merge(df_factors, on='IDBodenbedeckung')

        def rating(df, columns):
            df_rating = df.multiply(df['anteil']/100, axis='index')
            df_rating = df_rating[columns]
            df_rating = df_rating.sum(axis=0)
            n = self.MAX_RATING
            # divide the domain (0..1) into n + 1 bins
            # -> n is the max. rating value
            bins = np.linspace(0, 1, n+1)
            rating = np.digitize(df_rating, bins)
            return rating

        columns = df_factors.columns[3:]
        df_merged_nf = df_merged[df_merged['planfall']==False]
        df_merged_pf = df_merged[df_merged['planfall']==True]
        rating_nf = rating(df_merged_nf, columns)
        rating_pf = rating(df_merged_pf, columns)
        rating_delta = rating_pf - rating_nf
        columns = [c.replace('ae', 'ä').replace('ue', 'ü').replace('oe', 'ö')
                   .capitalize() for c in columns]

        diagram = Leistungskennwerte(
            nullfall=rating_nf, planfall=rating_pf,
            columns=columns, title='Leistungskennwerte Nullfall/Planfall',
            max_rating=self.MAX_RATING
        )
        diagram.draw()
        diagram = LeistungskennwerteDelta(
            delta=rating_delta, columns=columns,
            title='Leistungskennwerte Änderungen Planfall')
        diagram.draw()


