from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QMessageBox

from projektcheck.base.domain import Domain
from projektcheck.base.layers import TileLayer
from projektcheck.base.project import ProjectLayer
from projektcheck.base.tools import PolygonMapTool
from projektcheck.base.tools import FeaturePicker
from projektcheck.domains.ecology.tables import (BodenbedeckungNullfall,
                                                 BodenbedeckungPlanfall,
                                                 BodenbedeckungAnteile)
from projektcheck.base.params import (Params, Param, Title,
                                      Seperator, SumDependency)
from projektcheck.base.inputs import Slider
from projektcheck.utils.utils import clearLayout

from settings import settings


class Ecology(Domain):
    """"""

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
        self.feature_picker = FeaturePicker(self.ui.select_element_button,
                                            canvas=self.canvas)
        self.feature_picker.feature_picked.connect(self.feature_picked)
        self.ui.toggle_drawing_button.clicked.connect(self.add_output)
        self.layer_planfall = None
        self.layer_nullfall = None

        self.ui.planfall_radio.toggled.connect(self.toggle_planfall_nullfall)
        self.ui.planfall_radio.toggled.connect(self.add_output)
        self.toggle_planfall_nullfall()

        self.ui.remove_drawing_button.clicked.connect(self.clear_drawing)

    def toggle_planfall_nullfall(self):
        self.planfall = self.ui.planfall_radio.isChecked()
        l = self.layer_planfall if self.planfall else self.layer_nullfall
        self.feature_picker.set_layer(l)

    def load_content(self):
        self.boden_nullfall = BodenbedeckungNullfall.features(create=True)
        self.boden_planfall = BodenbedeckungPlanfall.features(create=True)
        self.anteile = BodenbedeckungAnteile.features(create=True)
        self.bb_types = self.basedata.get_table(
            'Bodenbedeckung', 'Flaeche_und_Oekologie'
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

        for params, prefix in [(self.params_nullfall, 'nullfall'),
                               (self.params_planfall, 'planfall')]:
            dependency = SumDependency(100)
            for bb_typ in self.bb_types.features():
                bb_id = bb_typ.IDBodenbedeckung
                feature = self.anteile.get(IDBodenbedeckung=bb_id,
                                           planfall=prefix=='planfall')
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
            self.ui.draw_trees_button: 4,
            self.ui.draw_perennial_button: 5,
            self.ui.draw_meadow_button: 6,
            self.ui.draw_lawn_button: 7,
            self.ui.draw_cover_button: 8,
            self.ui.draw_concrete_button: 9,
            self.ui.draw_field_button: 10,
            self.ui.draw_paving_button: 11
        }

        def add_geom(geom, floor_id):
            planfall = self.ui.planfall_radio.isChecked()
            coll = self.boden_planfall if planfall else self.boden_nullfall
            coll.add(geom=geom, IDBodenbedeckung=floor_id)
            self.canvas.refreshAllLayers()
            # workaround: layer style is not applied correctly
            # with empty features -> redraw on first geometry
            if len(coll) == 1:
                self.add_output()

        for button, floor_id in self.drawing_tools.items():
            tool = PolygonMapTool(button, canvas=self.canvas)
            tool.drawn.connect(
                lambda geom, i=floor_id: add_geom(geom, i))

        def cut_geom(clip_geom):
            planfall = self.ui.planfall_radio.isChecked()
            coll = self.boden_planfall if planfall else self.boden_nullfall
            layer = self.layer_planfall if self.planfall \
                else self.layer_nullfall
            features = layer.selectedFeatures()
            for qf in features:
                feat = coll.get(id=qf.id())
                #difference = clip_geom.makeDifference(feat.geom)
                # workaround: makeDifference seems to have a bug and returns the
                # intersection
                intersection = feat.geom.intersection(clip_geom)
                if intersection.isEmpty():
                    continue
                difference = feat.geom.symDifference(intersection)
                # ToDo: handle invalid and null geometries instead of ignoring
                if not difference.isNull():
                    feat.geom = difference
                    feat.save()
            self.canvas.refreshAllLayers()

        def remove_selected():
            planfall = self.ui.planfall_radio.isChecked()
            coll = self.boden_planfall if planfall else self.boden_nullfall
            layer = self.layer_planfall if self.planfall \
                else self.layer_nullfall
            ids = [f.id() for f in layer.selectedFeatures()]
            # remove selection, so that qgis is free to remove them from canvas
            layer.removeSelection()
            for fid in ids:
                feat = coll.get(id=fid)
                if feat:
                    feat.delete()
            self.canvas.refreshAllLayers()

        cutter = PolygonMapTool(
            self.ui.cut_element_button, canvas=self.canvas,
            color=QColor(255, 0, 0)
        )
        cutter.drawn.connect(cut_geom)
        self.ui.remove_element_button.clicked.connect(remove_selected)

    def clear_drawing(self):
        planfall = self.ui.planfall_radio.isChecked()
        l = 'Planfall' if planfall else 'Nullfall'
        reply = QMessageBox.question(
            self.ui, 'Zeichnung löschen',
            f'Sollen alle gezeichneten Flächen für den {l} entfernt werden?',
            QMessageBox.Yes, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            features = self.boden_planfall if planfall else self.boden_nullfall
            layer = self.layer_planfall if self.planfall \
                else self.layer_nullfall
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
        layer = output.draw(label=label, style_file=style)
        setattr(self, 'layer_planfall' if self.planfall else 'layer_nullfall',
                layer)
        self.toggle_planfall_nullfall()

    def add_wms_layer(self, name, url, parent_group=None):
        group = (f'{self.project.groupname}/{self.layer_group}')
        if parent_group:
            group += f'/{parent_group}'
        url = (f'{url}&crs=EPSG:{settings.EPSG}'
               '&format=image/png&dpiMode=7&styles')
        layer = TileLayer(url, groupname=group)
        layer.draw(name)

    def feature_picked(self, feature):
        layer = self.layer_planfall if self.planfall else self.layer_nullfall
        selected = [f.id() for f in layer.selectedFeatures()]
        if feature.id() not in selected:
            layer.select(feature.id())
        else:
            layer.removeSelection()
            layer.selectByIds([fid for fid in selected if fid != feature.id()])