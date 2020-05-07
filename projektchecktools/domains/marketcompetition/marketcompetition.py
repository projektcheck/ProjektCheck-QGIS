from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
import numpy as np

from projektchecktools.base.domain import Domain
from projektchecktools.base.project import ProjectLayer
from projektchecktools.domains.marketcompetition.tables import (
    Centers, Markets, MarketCellRelations)
from projektchecktools.domains.marketcompetition.read_osm import ReadOSMWorker
from projektchecktools.domains.marketcompetition.market_templates import (
    MarketTemplateCreateDialog, MarketTemplate, MarketTemplateImportWorker)
from projektchecktools.base.tools import FeaturePicker
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.base.params import Params, Param
from projektchecktools.base.inputs import LineEdit, ComboBox
from projektchecktools.utils.utils import center_canvas, clear_layout


class EditMarkets:
    layer_filter = ''
    layer_style = ''
    layer_label = ''
    filter_args = {}
    layer_group = 'Wirkungsbereich 8 - Standortkonkurrenz und Supermärkte'

    def __init__(self, combobox, select_button, param_group, canvas, project):
        self.combobox = combobox
        self.param_group = param_group
        self.select_button = select_button
        self.canvas = canvas
        self.project = project
        self.basedata = self.project.basedata
        self.layer = None
        self.params = None

    def setupUi(self):
        self.select_tool = FeaturePicker(
            self.select_button, canvas=self.canvas)
        self.select_tool.feature_picked.connect(
            self.select_market)
        self.select_button.clicked.connect(lambda: self.add_layer())
        self.combobox.currentIndexChanged.connect(
            lambda idx: self.toggle_market(self.combobox.currentData(),
            center_on_point=True)
        )

    def load_content(self):
        self.types = self.basedata.get_table(
            'Betriebstypen','Standortkonkurrenz_Supermaerkte'
        ).features()
        self.markets = Markets.features(create=True)
        self.fill_combo()

    def type_label(self, id_betriebstyp):
        typ = self.types.get(id_betriebstyp=id_betriebstyp)
        details = ''
        lower = typ.von_m2
        upper = typ.bis_m2
        if lower is not None:
            details = f'(ab {lower} m²'
            if upper is not None:
                details += f' bis {upper} m²'
            details += ' Verkaufsfläche)'
            details.replace('.', ',')
        pretty = f'{typ.name} {details}'
        return pretty

    def fill_combo(self, select=None):
        self.combobox.blockSignals(True)
        self.combobox.clear()
        self.combobox.addItem('nichts ausgewählt')
        idx = 0
        nullfall_markets = self.markets.filter(**self.filter_args)
        for i, market in enumerate(nullfall_markets):
            self.combobox.addItem(
                market.name,
                market
            )
            if select and market.id == select.id:
                idx = i + 1
        if idx:
            self.comboboxsetCurrentIndex(idx)
        self.combobox.blockSignals(False)
        self.toggle_market(self.combobox.currentData())

    def select_market(self, feature):
        if not self.layer:
            return
        self.layer.removeSelection()
        self.layer.select(feature.id())
        fid = feature.id()
        for idx in range(len(self.combobox)):
            market = self.combobox.itemData(idx)
            if market and fid == market.id:
                break
        self.combobox.setCurrentIndex(idx)

    def toggle_market(self, market, center_on_point=False):
        if not market:
            return
        if self.layer:
            self.layer.removeSelection()
            self.layer.select(market.id)
            if center_on_point:
                center_canvas(self.canvas, market.geom.asPoint(),
                              self.layer.crs())
        self.setup_params(market)

    def setup_params(self, market):
        raise NotImplementedError

    def add_layer(self, zoom_to=False):
        output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        self.layer = output.draw(
            label=self.layer_label,
            style_file=self.layer_style,
            filter=self.layer_filter
        )
        self.select_tool.set_layer(self.layer)
        if zoom_to:
            output.zoom_to()

    def close(self):
        pass


class EditNullfallMarkets(EditMarkets):
    layer_filter = 'id_betriebstyp_nullfall > 0'
    layer_style = 'standortkonkurrenz_maerkte_im_bestand.qml'
    layer_label = 'Märkte im Bestand'
    filter_args = {'id_betriebstyp_nullfall__gt': 0}

    def setup_params(self, market):
        if self.params:
            self.params.close()
        layout = self.param_group.layout()
        clear_layout(layout)
        if not market:
            return
        self.params = Params(
            layout)# , help_file='infrastruktur_punktmassnahme.txt')
        self.params.name = Param(
            market.name, LineEdit(width=300),
            label='Name')

        type_ids = [typ.id_betriebstyp for typ in self.types]
        type_labels = [self.type_label(i) for i in type_ids]

        type_combo = ComboBox(type_labels, data=type_ids, width=300)
        #id_betriebstyp_nullfall
        self.params.typ = Param(
            self.type_label(market.id_betriebstyp_nullfall), type_combo,
            label='Betriebstyp'
        )

        self.params.show()
        #self.point_params.changed.connect(save)


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
            lambda: self.show_markets(zoom_to=True))

        self.ui.remove_osm_button.clicked.connect(
            lambda: self.remove_markets(osm_only=True))
        self.ui.remove_markets_button.clicked.connect(
            lambda: self.remove_markets(osm_only=False))
        self.ui.add_osm_button.clicked.connect(self.add_osm)

        self.nullfall_edit = EditNullfallMarkets(
            self.ui.nullfall_market_combo,
            self.ui.select_nullfall_market_button,
            self.ui.nullfall_market_parameter_group,
            self.canvas,
            self.project
        )
        self.nullfall_edit.setupUi()

    def load_content(self):
        self.centers = Centers.features()
        self.markets = Markets.features(create=True)
        self.relations = MarketCellRelations.features(create=True)
        self.nullfall_edit.load_content()

    def show_markets(self, zoom_to=True):
        self.nullfall_edit.add_layer(zoom_to=zoom_to)
        #output = ProjectLayer.from_table(
            #self.markets.table, groupname=self.layer_group)
        #self.nullfall_markets_layer = output.draw(
            #label='Märkte im Bestand',
            #style_file='standortkonkurrenz_maerkte_im_bestand.qml',
            #filter='id_betriebstyp_nullfall > 0'
        #)
        #self.select_nullfall_market_tool.set_layer(self.nullfall_markets_layer)
        #if zoom_to:
            #output.zoom_to()
        #output = ProjectLayer.from_table(
            #self.markets.table, groupname=self.layer_group)
        #self.planfall_markets_layer = output.draw(
            #label='geplante Märkte',
            #style_file='standortkonkurrenz_geplante_maerkte.qml',
            #filter='id_betriebstyp_nullfall = 0'
        #)
        #output = ProjectLayer.from_table(
            #self.markets.table, groupname=self.layer_group)
        #self.changed_markets_layer = output.draw(
            #label='veränderte Märkte im Bestand',
            #style_file='standortkonkurrenz_veraenderte_maerkte.qml',
            ## ToDo: that's wrong
            #filter='id_betriebstyp_nullfall > 0 and '
            #'id_betriebstyp_nullfall != id_betriebstyp_planfall > 0'
        #)

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

    def close(self):
        self.community_picker.set_active(False)
        super().close()

