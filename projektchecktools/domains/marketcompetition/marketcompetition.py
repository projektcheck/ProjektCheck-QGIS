from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.Qt import QPushButton
from qgis.PyQt.QtGui import QIcon
import os
import numpy as np

from projektchecktools.base.domain import Domain
from projektchecktools.base.project import ProjectLayer
from projektchecktools.domains.marketcompetition.tables import (
    Centers, Markets, MarketCellRelations)
from projektchecktools.domains.marketcompetition.read_osm import ReadOSMWorker
from projektchecktools.domains.marketcompetition.market_templates import (
    MarketTemplateCreateDialog, MarketTemplate, MarketTemplateImportWorker)
from projektchecktools.base.tools import FeaturePicker, MapClickedTool
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.base.params import Params, Param, Seperator
from projektchecktools.base.inputs import LineEdit, ComboBox
from projektchecktools.utils.utils import center_canvas, clear_layout, get_ags


class EditMarkets:
    layer_filter = ''
    layer_style = ''
    filter_args = {}
    layer_group = 'Wirkungsbereich 8 - Standortkonkurrenz und Supermärkte'
    market_label = ''
    suffix = ''

    def __init__(self, combobox, select_button, param_group, canvas, project,
                 add_button=None, remove_button=None):
        self.combobox = combobox
        self.param_group = param_group
        self.select_button = select_button
        self.canvas = canvas
        self.project = project
        self.basedata = self.project.basedata
        self.add_button = add_button
        self.remove_button = remove_button
        self.layer = None
        self.params = None
        self.add_market_tool = None

    def setupUi(self):
        self.select_tool = FeaturePicker(self.select_button, canvas=self.canvas)
        self.select_tool.feature_picked.connect(self.select_market)
        self.select_button.clicked.connect(lambda: self.add_layer())
        self.combobox.currentIndexChanged.connect(
            lambda idx: self.toggle_market(self.combobox.currentData(),
            center_on_point=True)
        )
        if self.add_button:
            self.add_market_tool = MapClickedTool(
                self.add_button, canvas=self.canvas,
                target_epsg=self.project.settings.EPSG)
            self.add_market_tool.map_clicked.connect(self.add_market)
            self.add_button.clicked.connect(lambda: self.add_layer())
        if self.remove_button:
            self.remove_button.clicked.connect(
                lambda: self.remove_markets())

    def load_content(self):
        self.typen = self.basedata.get_table(
            'Betriebstypen','Standortkonkurrenz_Supermaerkte'
        ).features()
        self.ketten = self.basedata.get_table(
            'Ketten','Standortkonkurrenz_Supermaerkte'
        ).features()
        self.markets = Markets.features(create=True)
        self.fill_combo()

    def detailed_type_label(self, id_betriebstyp):
        typ = self.typen.get(id_betriebstyp=id_betriebstyp)
        details = ''
        lower = typ.von_m2
        upper = typ.bis_m2
        if lower is not None:
            details = f'(ab {lower} m²'
            if upper is not None:
                details += f' bis {upper} m²'
            details += ' Verkaufsfläche)'
            details.replace('.', ',')
        label = f'{typ.name} {details}'
        return label

    def detailed_market_label(self, market):
        typ = market[f'betriebstyp_{self.suffix}']
        osm = ' OSM' if market.is_osm else ''
        kette = market.kette if market.kette != 'nicht aufgeführt' \
            else 'Anbieter unbekannt'
        label = (f'{market.name}{osm} ({market.id}) - {typ} ({kette})')
        return label

    def fill_combo(self, select=None):
        self.combobox.blockSignals(True)
        self.combobox.clear()
        self.combobox.addItem('nichts ausgewählt')
        idx = 0
        markets = [m for m in self.markets.filter(**self.filter_args)]
        markets_sorted = sorted(markets, key=lambda m: m.AGS or ' ')
        for i, market in enumerate(markets_sorted):
            self.combobox.addItem(self.detailed_market_label(market), market)
            if select and market.id == select.id:
                idx = i + 1
        if idx:
            self.combobox.setCurrentIndex(idx)
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
            label=self.market_label,
            style_file=self.layer_style,
            filter=self.layer_filter
        )
        self.select_tool.set_layer(self.layer)
        if zoom_to:
            output.zoom_to()

    def add_market(self, geom):
        raise NotImplementedError

    def remove_market(self, market):
        if not market:
            return
        reply = QMessageBox.question(
            self.param_group, 'Markt entfernen',
            f'Soll der Markt "{market.name} ({market.kette})" '
            'entfernt werden?\n',
             QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            market.delete()
            self.canvas.refreshAllLayers()
            self.fill_combo()

    def remove_markets(self):
        reply = QMessageBox.question(
            self.param_group, f'{self.market_label} löschen',
            f'Möchten Sie alle {self.market_label} löschen?',
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.markets.filter(**self.filter_args).delete()
            markets.delete()
            self.canvas.refreshAllLayers()
            self.fill_combo()

    def close(self):
        if self.add_market_tool:
            self.add_market_tool.set_active(False)
        if self.params:
            self.params.close()


class EditNullfallMarkets(EditMarkets):
    layer_filter = 'id_betriebstyp_nullfall > 0'
    layer_style = 'standortkonkurrenz_maerkte_im_bestand.qml'
    filter_args = {'id_betriebstyp_nullfall__gt': 0}
    market_label = 'Märkte im Bestand'
    suffix = 'nullfall'

    def setup_params(self, market):
        if self.params:
            self.params.close()
        layout = self.param_group.layout()
        clear_layout(layout)
        if not market:
            return
        self.params = Params(layout, help_file='standortkonkurrenz_bestand.txt')
        self.params.name = Param(
            market.name, LineEdit(width=300),
            label='Name')

        self.params.add(Seperator(margin=0))

        type_ids = [typ.id_betriebstyp for typ in self.typen]
        type_labels = [self.detailed_type_label(i) for i in type_ids]
        type_combo = ComboBox(type_labels, data=type_ids, width=300)

        self.params.typ = Param(
            self.detailed_type_label(market.id_betriebstyp_nullfall),
            type_combo, label='Betriebstyp im Nullfall',
            value_label=market.betriebstyp_nullfall
        )

        # 'nicht aufgeführt' (kette 0) is first, rest alphabetical order
        ketten = sorted(self.ketten, key=lambda k: k.name
                        if k.name != 'nicht aufgeführt' else '')
        chain_ids = [typ.id_kette for typ in ketten]
        chain_labels = [kette.name for kette in ketten]
        chain_combo = ComboBox(chain_labels, data=chain_ids, width=300)
        value = self.ketten.get(id_kette=market.id_kette).name

        self.params.kette = Param(value, chain_combo, label='Anbieter')

        def save():
            market.name = self.params.name.value
            id_bt = type_combo.get_data()
            bt = self.typen.get(id_betriebstyp=id_bt).name
            market.id_betriebstyp_nullfall = id_bt
            market.betriebstyp_nullfall = bt
            # planfall is also set to same type -> possible planned change is
            # overwritten
            market.id_betriebstyp_planfall = id_bt
            market.betriebstyp_planfall = bt
            market.id_kette = chain_combo.get_data()
            market.kette = self.ketten.get(id_kette=market.id_kette).name
            market.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_combo(select=market)

        self.params.show(title='Markt im Bestand bearbeiten')
        self.params.changed.connect(save)

        last_row = self.params.layout.children()[-1]
        button = QPushButton()
        icon_path = 'iconset_mob/20190619_iconset_mob_delete_1.png'
        icon = QIcon(os.path.join(self.project.settings.IMAGE_PATH, icon_path))
        button.setText('Markt entfernen')
        button.setIcon(icon)
        button.setToolTip(
            '<p><span style=" font-weight:600;">Markt entfernen</span>'
            '</p><p>Löscht den aktuell gewählten Markt. '
            '<br/>Dieser Schritt kann nicht rückgängig gemacht werden. </p>')
        last_row.insertWidget(0, button)
        button.clicked.connect(lambda: self.remove_market(market))

    def add_market(self, geom, name='unbenannter Markt im Bestand'):
        id_bt = 1
        bt = self.typen.get(id_betriebstyp=id_bt).name
        market = self.markets.add(
            name=name,
            id_betriebstyp_nullfall=id_bt,
            betriebstyp_nullfall=bt,
            id_betriebstyp_planfall=id_bt,
            betriebstyp_planfall=bt,
            id_kette=0,
            kette=self.ketten.get(id_kette=0).name,
            geom=geom
        )
        crs = QgsCoordinateReferenceSystem(f'EPSG:{self.project.settings.EPSG}')
        ags = get_ags([market], self.basedata, source_crs=crs)[0]
        market.AGS = ags.AGS_0
        market.save()
        self.canvas.refreshAllLayers()
        self.fill_combo(select=market)


class EditPlanfallMarkets(EditMarkets):
    layer_filter = 'id_betriebstyp_nullfall = 0'
    layer_style = 'standortkonkurrenz_geplante_maerkte.qml'
    filter_args = {'id_betriebstyp_nullfall': 0}
    market_label = 'geplante Märkte'
    suffix = 'planfall'

    def setup_params(self, market):
        # ToDo: that's mostly the same as in EditNullfallMarkets,
        # might be merged
        if self.params:
            self.params.close()
        layout = self.param_group.layout()
        clear_layout(layout)
        if not market:
            return
        self.params = Params(
            layout, help_file='standortkonkurrenz_geplante_maerkte.txt')

        self.params.name = Param(
            market.name, LineEdit(width=300),
            label='Name')

        self.params.add(Seperator(margin=0))

        type_ids = [typ.id_betriebstyp for typ in self.typen]
        type_labels = [self.detailed_type_label(i) for i in type_ids]
        type_combo = ComboBox(type_labels, data=type_ids, width=300)

        self.params.typ = Param(
            self.detailed_type_label(market.id_betriebstyp_planfall),
            type_combo, label='Betriebstyp im Planfall',
            value_label=market.betriebstyp_planfall
        )

        # 'nicht aufgeführt' (kette 0) is first, rest alphabetical order
        ketten = sorted(self.ketten, key=lambda k: k.name
                        if k.name != 'nicht aufgeführt' else '')
        chain_ids = [typ.id_kette for typ in ketten]
        chain_labels = [kette.name for kette in ketten]
        chain_combo = ComboBox(chain_labels, data=chain_ids, width=300)
        value = self.ketten.get(id_kette=market.id_kette).name

        self.params.kette = Param(value, chain_combo, label='Anbieter')

        def save():
            market.name = self.params.name.value
            id_bt = type_combo.get_data()
            bt = self.typen.get(id_betriebstyp=id_bt).name
            market.id_betriebstyp_planfall = id_bt
            market.betriebstyp_planfall = bt
            market.id_kette = chain_combo.get_data()
            market.kette = self.ketten.get(id_kette=market.id_kette).name
            market.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_combo(select=market)

        self.params.show(title='Markt im Bestand bearbeiten')
        self.params.changed.connect(save)

        last_row = self.params.layout.children()[-1]
        button = QPushButton()
        icon_path = 'iconset_mob/20190619_iconset_mob_delete_1.png'
        icon = QIcon(os.path.join(self.project.settings.IMAGE_PATH, icon_path))
        button.setText('Markt entfernen')
        button.setIcon(icon)
        button.setToolTip(
            '<p><span style=" font-weight:600;">Markt entfernen</span>'
            '</p><p>Löscht den aktuell gewählten Markt. '
            '<br/>Dieser Schritt kann nicht rückgängig gemacht werden. </p>')
        last_row.insertWidget(0, button)
        button.clicked.connect(lambda: self.remove_market(market))

    def add_market(self, geom, name='unbenannter geplanter Markt'):
        market = self.markets.add(
            name=name,
            id_betriebstyp_nullfall=0,
            betriebstyp_nullfall=self.typen.get(id_betriebstyp=0).name,
            id_betriebstyp_planfall=1,
            betriebstyp_planfall=self.typen.get(id_betriebstyp=1).name,
            id_kette=0,
            kette=self.ketten.get(id_kette=0).name,
            geom=geom
        )
        crs = QgsCoordinateReferenceSystem(f'EPSG:{self.project.settings.EPSG}')
        ags = get_ags([market], self.basedata, source_crs=crs)[0]
        market.AGS = ags.AGS_0
        market.save()
        self.canvas.refreshAllLayers()
        self.fill_combo(select=market)


class ChangeMarkets(EditMarkets):
    layer_filter = ('id_betriebstyp_nullfall != id_betriebstyp_planfall '
                    'and id_betriebstyp_nullfall > 0')
    layer_style = 'standortkonkurrenz_veraenderte_maerkte.qml'
    filter_args = {'id_betriebstyp_nullfall__gt': 0}
    market_label = 'veränderte Märkte im Bestand'
    suffix = 'nullfall'

    def setup_params(self, market):
        if self.params:
            self.params.close()
        layout = self.param_group.layout()
        clear_layout(layout)
        if not market:
            return
        self.params = Params(
            layout, help_file='standortkonkurrenz_veraenderte_maerkte.txt')
        self.params.name = Param(market.name, label='Name')

        self.params.add(Seperator(margin=0))

        self.params.kette = Param(market.kette, label='Anbieter')

        self.params.nullfall = Param(
            market.betriebstyp_nullfall,
            label='Betriebstyp im Nullfall',
        )

        type_ids = [typ.id_betriebstyp for typ in self.typen]
        type_labels = [self.detailed_type_label(i) for i in type_ids]
        type_combo = ComboBox(type_labels, data=type_ids, width=300)

        self.params.planfall = Param(
            self.detailed_type_label(market.id_betriebstyp_planfall),
            type_combo, label='Betriebstyp im Planfall',
            value_label=market.betriebstyp_planfall
        )

        def save():
            id_bt = type_combo.get_data()
            bt = self.typen.get(id_betriebstyp=id_bt).name
            market.id_betriebstyp_planfall = id_bt
            market.betriebstyp_planfall = bt
            market.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_combo(select=market)

        self.params.show(title='Markt im Planfall verändern')
        self.params.changed.connect(save)


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

        self.ui.add_osm_button.clicked.connect(self.add_osm)
        self.ui.remove_osm_button.clicked.connect(self.remove_osm)

        self.nullfall_edit = EditNullfallMarkets(
            self.ui.nullfall_market_combo,
            self.ui.select_nullfall_market_button,
            self.ui.nullfall_market_parameter_group,
            self.canvas,
            self.project,
            remove_button=self.ui.remove_planfall_markets_button,
            add_button=self.ui.add_nullfall_market_button
        )
        self.nullfall_edit.setupUi()

        self.planfall_edit = EditPlanfallMarkets(
            self.ui.planfall_market_combo,
            self.ui.select_planfall_market_button,
            self.ui.planfall_market_parameter_group,
            self.canvas, self.project,
            remove_button=self.ui.remove_planfall_markets_button,
            add_button=self.ui.add_planfall_market_button
        )
        self.planfall_edit.setupUi()

        self.changed_edit = ChangeMarkets(
            self.ui.changed_market_combo,
            self.ui.select_changed_market_button,
            self.ui.changed_market_parameter_group,
            self.canvas, self.project
        )
        self.changed_edit.setupUi()

    def load_content(self):
        self.centers = Centers.features()
        self.markets = Markets.features(create=True)
        self.relations = MarketCellRelations.features(create=True)
        self.nullfall_edit.load_content()
        self.planfall_edit.load_content()
        self.changed_edit.load_content()

    def show_markets(self, zoom_to=True):
        self.planfall_edit.add_layer()
        self.changed_edit.add_layer()
        self.nullfall_edit.add_layer(zoom_to=zoom_to)

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

    def remove_osm(self):
        reply = QMessageBox.question(
            self.ui, 'OSM-Märkte löschen',
            f'Möchten Sie alle OSM-Märkte löschen?',
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.markets.filter(is_osm=True).delete()
            self.fill_combo()
            self.canvas.refreshAllLayers()

    def close(self):
        self.community_picker.set_active(False)
        self.nullfall_edit.close()
        self.planfall_edit.close()
        self.changed_edit.close()
        super().close()

