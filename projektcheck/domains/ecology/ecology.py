from projektcheck.base.domain import Domain
from projektcheck.base.layers import TileLayer
from projektcheck.base.tools import PolygonMapTool
from projektcheck.domains.ecology.tables import (BodenbedeckungNullfall,
                                                 BodenbedeckungPlanfall)

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

    def load_content(self):
        self.boden_nullfall = BodenbedeckungNullfall.features(create=True)
        self.boden_planfall = BodenbedeckungPlanfall.features(create=True)

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

        self.ui.paint_tool_frame.setVisible(False)

    def setup_drawing_tools(self):
        return
        self.drawing_tools = {}
        self.drawing_tools[self.draw_builtup_button] = 'a'
        self.builtup_tool = PolygonMapTool(self.canvas)
        self.draw_builtup_button.clicked.connect()

    def add_wms_layer(self, name, url, parent_group=None):
        group = (f'{self.project.groupname}/{self.layer_group}')
        if parent_group:
            group += f'/{parent_group}'
        url = (f'{url}&crs=EPSG:{settings.EPSG}'
               '&format=image/png&dpiMode=7&styles')
        layer = TileLayer(url, groupname=group)
        layer.draw(name)