from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox

from projektchecktools.base.domain import Domain
from projektchecktools.base.project import ProjectLayer
from projektchecktools.domains.marketcompetition.tables import (
    Centers, Markets, MarketCellRelations)
from projektchecktools.domains.marketcompetition.read_osm import ReadOSMWorker
from projektchecktools.domains.marketcompetition.market_templates import (
    MarketTemplateCreateDialog, MarketTemplate, MarketTemplateImportWorker)
from projektchecktools.base.tools import FeaturePicker
from projektchecktools.base.dialogs import ProgressDialog


class SupermarketsCompetition(Domain):
    """"""

    ui_label = 'Standortkonkurrenz und Supermärkte'
    ui_file = 'ProjektCheck_dockwidget_analysis_08-SKSM.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_supermarkets_1.png"

    layer_group = 'Wirkungsbereich 8 - Standortkonkurrenz und Supermärkte'

    def setupUi(self):
        self.community_picker = FeaturePicker(self.ui.select_communities_button,
                                              canvas=self.canvas)
        self.community_picker.feature_picked.connect(self.community_picked)

        self.ui.create_template_button.clicked.connect(
            lambda: MarketTemplateCreateDialog().show())
        self.ui.read_template_button.clicked.connect(self.read_template)
        self.ui.select_communities_button.clicked.connect(
            lambda: self.show_communities(
                zoom_to=self.ui.select_communities_button.isChecked()))
        self.ui.show_markets_button.clicked.connect(
            lambda: self.show_markets(
                zoom_to=self.ui.show_markets_button.isChecked()))

        self.ui.remove_osm_button.clicked.connect(self.remove_osm)
        self.ui.add_osm_button.clicked.connect(self.add_osm)

    def load_content(self):
        self.centers = Centers.features()
        self.markets = Markets.features(create=True)
        self.relations = MarketCellRelations.features(create=True)

    def show_communities(self, zoom_to=True):
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.centers_selected_layer = output.draw(
            label='Ausgewählte Gemeinden im Betrachtungsraum',
            style_file='standortkonkurrenz_gemeinden_ausgewaehlt.qml',
            filter='auswahl=1 AND nutzerdefiniert=-1'
        )
        self.community_picker.set_layer(self.centers_selected_layer)

        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.centers_not_selected_layer = output.draw(
            label='Nicht ausgewählte Gemeinden',
            style_file='standortkonkurrenz_gemeinden_nicht_ausgewaehlt.qml',
            filter='auswahl=0 AND nutzerdefiniert=-1'
        )
        self.community_picker.add_layer(self.centers_not_selected_layer)
        if zoom_to:
            output.zoom_to()

    def show_markets(self, zoom_to=True):
        output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        output.draw(
            label='Märkte im Bestand',
            style_file='standortkonkurrenz_maerkte_im_bestand.qml',
            filter='id_betriebstyp_nullfall > 0'
        )
        if zoom_to:
            output.zoom_to()
        output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        output.draw(
            label='geplante Märkte',
            style_file='standortkonkurrenz_geplante_maerkte.qml',
            filter='id_betriebstyp_nullfall = 0'
        )
        output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        output.draw(
            label='veränderte Märkte im Bestand',
            style_file='standortkonkurrenz_veraenderte_maerkte.qml',
            filter='id_betriebstyp_nullfall > 0 and id_betriebstyp_planfall > 0'
        )

    def community_picked(self, feature):
        center = self.centers.get(id=feature.id())
        center.auswahl = not center.auswahl
        center.save()
        self.canvas.refreshAllLayers()

    def read_template(self):
        filters = [f'*{ext[0]}' for ext
                   in MarketTemplate.template_types.values()]
        path, f = QFileDialog.getOpenFileName(
            self.ui, 'Templatedatei öffnen', None,
            f'Templatedatei ({" ".join(filters)})'
        )
        if path:
            job = MarketTemplateImportWorker(path, self.project,
                                             epsg=self.settings.EPSG)
            dialog = ProgressDialog(
                job, parent=self.ui,
                on_success=lambda project: self.canvas.refreshAllLayers())
            dialog.show()

    def add_osm(self):
        job = ReadOSMWorker(self.project, epsg=self.settings.EPSG,
                            truncate=self.ui.truncate_osm_check.isChecked())
        dialog = ProgressDialog(
            job, parent=self.ui,
            on_success=lambda: self.canvas.refreshAllLayers())
        dialog.show()

    def remove_osm(self):
        reply = QMessageBox.question(
            self.ui, 'OSM-Märkte löschen',
            'Möchten Sie alle aus OSM ermittelten Märkte löschen?',
             QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.markets.filter(is_osm=True).delete()
            self.canvas.refreshAllLayers()

    def close(self):
        self.community_picker.set_active(False)
        super().close()

