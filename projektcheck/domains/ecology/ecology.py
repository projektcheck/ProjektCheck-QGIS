from projektcheck.base.domain import Domain
from projektcheck.base.layers import TileLayer

from settings import settings


class Ecology(Domain):
    """"""

    ui_label = 'Ökologie'
    ui_file = 'ProjektCheck_dockwidget_analysis_04-Oeko.ui'
    ui_icon = ('images/iconset_mob/'
               '20190619_iconset_mob_nature_conservation_2.png')

    layer_group = 'Wirkungsbereich 4 - Ökologie'
    geoserver = 'https://geoserver.ggr-planung.de/geoserver/projektcheck/wms?'
    nature_layers = {
        'Naturschutzgebiete': f'url={geoserver}&layers=nsg_2017',
        'FFH-Gebiete': f'url={geoserver}&layers=ffh_de_2018',
        'Nationalparke': f'url={geoserver}&layers=nlp2019',
        'Nationale Naturmonumente': f'url={geoserver}&layers=nnm_2019',
        'RAMSAR-Gebiete': f'url={geoserver}&layers=ramsar2013',
        'Vogelschutzgebiete': f'url={geoserver}&layers=spa_de_2018',
    }

    def setupUi(self):
        self.ui.nature_button.clicked.connect(
            lambda: self.add_wms_layers(
                self.nature_layers, parent_group='Natur- und Artenschutz')
        )

    def load_content(self):
        pass

    def add_wms_layers(self, layer_dict, parent_group=None):
        group = (f'{self.project.groupname}/{self.layer_group}')
        if parent_group:
            group += f'/{parent_group}'
        for name, url in layer_dict.items():
            url = (f'{url}&crs=EPSG:{settings.EPSG}'
                   '&format=image/png&dpiMode=7&styles')
            layer = TileLayer(url, groupname=group)
            layer.draw(name)