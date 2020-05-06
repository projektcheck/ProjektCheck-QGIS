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
from projektchecktools.utils.utils import center_canvas


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

        self.ui.remove_osm_button.clicked.connect(
            lambda: self.remove_markets(osm_only=True))
        self.ui.remove_markets_button.clicked.connect(
            lambda: self.remove_markets(osm_only=False))
        self.ui.add_osm_button.clicked.connect(self.add_osm)

        self.select_nullfall_market_tool = FeaturePicker(
            self.ui.select_nullfall_market_button, canvas=self.canvas)
        self.select_nullfall_market_tool.feature_picked.connect(
            self.select_nullfall_market)
        self.ui.select_nullfall_market_button.clicked.connect(
            lambda: self.show_markets())
        self.ui.nullfall_market_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_nullfall_market(
                self.ui.nullfall_market_combo.currentData(),
            center_on_point=True))
        self.nullfall_markets_layer = None
        self.planfall_markets_layer = None
        self.changed_markets_layer = None

    def load_content(self):
        self.centers = Centers.features()
        self.markets = Markets.features(create=True)
        self.relations = MarketCellRelations.features(create=True)
        self.fill_nullfall_market_combo()

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
        self.nullfall_markets_layer = output.draw(
            label='Märkte im Bestand',
            style_file='standortkonkurrenz_maerkte_im_bestand.qml',
            filter='id_betriebstyp_nullfall > 0'
        )
        self.select_nullfall_market_tool.set_layer(self.nullfall_markets_layer)
        if zoom_to:
            output.zoom_to()
        output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        self.planfall_markets_layer = output.draw(
            label='geplante Märkte',
            style_file='standortkonkurrenz_geplante_maerkte.qml',
            filter='id_betriebstyp_nullfall = 0'
        )
        output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        self.changed_markets_layer = output.draw(
            label='veränderte Märkte im Bestand',
            style_file='standortkonkurrenz_veraenderte_maerkte.qml',
            # ToDo: that's wrong
            filter='id_betriebstyp_nullfall > 0 and '
            'id_betriebstyp_nullfall != id_betriebstyp_planfall > 0'
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
            def on_success(r):
                self.fill_nullfall_market_combo()
                self.show_markets(zoom_to=True)
            job = MarketTemplateImportWorker(path, self.project,
                                             epsg=self.settings.EPSG)
            dialog = ProgressDialog(job, parent=self.ui, on_success=on_success)
            dialog.show()

    def add_osm(self):
        job = ReadOSMWorker(self.project, epsg=self.settings.EPSG,
                            truncate=self.ui.truncate_osm_check.isChecked())
        def on_success(r):
            self.fill_nullfall_market_combo()
            self.show_markets(zoom_to=True)
        dialog = ProgressDialog( job, parent=self.ui, on_success=on_success)
        dialog.show()

    def remove_markets(self, osm_only=False):
        txt = 'OSM-Märkte' if osm_only else 'Märkte im Bestand'
        reply = QMessageBox.question(
            self.ui, f'{txt} löschen',
            f'Möchten Sie alle {txt} löschen?',
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            markets = self.markets.filter(is_osm=True) if osm_only \
                else self.markets.filter(id_betriebstyp_nullfall__gt=0)
            markets.delete()
            self.fill_nullfall_market_combo()
            self.canvas.refreshAllLayers()

    def fill_nullfall_market_combo(self, select=None):
        self.ui.nullfall_market_combo.blockSignals(True)
        self.ui.nullfall_market_combo.clear()
        self.ui.nullfall_market_combo.addItem('nichts ausgewählt')
        idx = 0
        nullfall_markets = self.markets.filter(id_betriebstyp_nullfall__gt=0)
        for i, market in enumerate(nullfall_markets):
            self.ui.nullfall_market_combo.addItem(
                market.name,
                market
            )
            if select and market.id == select.id:
                idx = i + 1
        if idx:
            self.ui.nullfall_market_combo.setCurrentIndex(idx)
        self.ui.nullfall_market_combo.blockSignals(False)
        self.toggle_nullfall_market(self.ui.nullfall_market_combo.currentData())

    def select_nullfall_market(self, feature):
        if not self.nullfall_markets_layer:
            return
        self.nullfall_markets_layer.removeSelection()
        self.nullfall_markets_layer.select(feature.id())
        fid = feature.id()
        for idx in range(len(self.ui.nullfall_market_combo)):
            market = self.ui.nullfall_market_combo.itemData(idx)
            if market and fid == market.id:
                break
        self.ui.nullfall_market_combo.setCurrentIndex(idx)

    def toggle_nullfall_market(self, market, center_on_point=False):
        if not market:
            return
        if self.nullfall_markets_layer:
            self.nullfall_markets_layer.removeSelection()
            self.nullfall_markets_layer.select(market.id)
            if center_on_point:
                center_canvas(self.canvas, market.geom.asPoint(),
                              self.nullfall_markets_layer.crs())
        self.setup_nullfall_market_params(market)

    def setup_nullfall_market_params(self, market):
        pass

    def close(self):
        self.community_picker.set_active(False)
        super().close()

