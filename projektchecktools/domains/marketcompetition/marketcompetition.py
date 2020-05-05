from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox

from projektchecktools.base.domain import Domain
from projektchecktools.base.project import ProjectLayer
from projektchecktools.domains.marketcompetition.tables import Centers, Markets
from projektchecktools.domains.marketcompetition.read_osm import ReadOSMWorker
from projektchecktools.domains.marketcompetition.market_templates import (
    MarketTemplateCreateDialog, MarketTemplate)
from projektchecktools.base.tools import FeaturePicker


class SupermarketsCompetition(Domain):
    """"""

    ui_label = 'Standortkonkurrenz und Supermärkte'
    ui_file = 'ProjektCheck_dockwidget_analysis_08-SKSM.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_supermarkets_1.png"

    layer_group = 'Wirkungsbereich 8 - Standortkonkurrenz und Supermärkte'

    def setupUi(self):
        self.center_picker = FeaturePicker(self.ui.select_centers_button,
                                           canvas=self.canvas)
        self.center_picker.feature_picked.connect(self.center_picked)

        self.ui.create_template_button.clicked.connect(
            lambda: MarketTemplateCreateDialog().show())
        self.ui.read_template_button.clicked.connect(self.read_template)
        self.ui.select_centers_button.clicked.connect(
            lambda: self.draw_gem(zoom_to=True))
        self.ui.add_osm_button.clicked.connect(self.add_osm)

    def load_content(self):
        self.centers = Centers.features()
        self.markets = Markets.features(create=True)

    def draw_gem(self, zoom_to=True):
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.centers_selected_layer = output.draw(
            label='Ausgewählte Gemeinden im Betrachtungsraum',
            style_file='standortkonkurrenz_gemeinden_ausgewaehlt.qml',
            filter='auswahl=1 AND nutzerdefiniert=-1'
        )
        self.center_picker.set_layer(self.centers_selected_layer)

        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.centers_not_selected_layer = output.draw(
            label='Nicht ausgewählte Gemeinden',
            style_file='standortkonkurrenz_gemeinden_nicht_ausgewaehlt.qml',
            filter='auswahl=0 AND nutzerdefiniert=-1'
        )
        self.center_picker.add_layer(self.centers_not_selected_layer)
        if zoom_to:
            output.zoom_to()

    def center_picked(self, feature):
        center = self.centers.get(id=feature.id())
        center.auswahl = not center.auswahl
        center.save()
        self.canvas.refreshAllLayers()

    def read_template(self):
        filters = [f'*{ext[0]}' for ext
                   in MarketTemplate.template_types.values()]
        path, f = QFileDialog.getOpenFileName(
            self.ui, 'Templatedatei öffnen', None,
            f'Templatedatei ({",".join(filters)})'
        )

    def add_osm(self):
        job = ReadOSMWorker(self.project, epsg=self.settings.EPSG)
        job.work()
        #dialog = ProgressDialog(
            #job, parent=self.ui,
            #on_success=lambda project: on_success(project, date))
        #dialog.show()

    def close(self):
        self.center_picker.set_active(False)
        super().close()

