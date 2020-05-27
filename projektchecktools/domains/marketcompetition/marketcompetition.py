from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.Qt import QPushButton
from qgis.PyQt.QtCore import QObject, pyqtSignal
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
from projektchecktools.base.tools import (FeaturePicker, MapClickedTool,
                                          PolygonMapTool)
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.base.params import Params, Param, Seperator
from projektchecktools.base.inputs import LineEdit, ComboBox, Checkbox
from projektchecktools.utils.utils import (center_canvas, clear_layout,
                                           get_ags, open_file)
from projektchecktools.domains.marketcompetition.projektwirkung import (
    Projektwirkung)


class EditMarkets(QObject):
    layer_filter = ''
    layer_style = ''
    filter_args = {}
    layer_group = 'Wirkungsbereich 8 - Standortkonkurrenz und Supermärkte'
    market_label = ''
    suffix = ''
    show_change = False
    changed = pyqtSignal()

    def __init__(self, combobox, select_button, param_group, canvas, project,
                 add_button=None, remove_button=None):
        super().__init__()
        self.combobox = combobox
        self.param_group = param_group
        self.select_button = select_button
        self.canvas = canvas
        self.project = project
        self.basedata = self.project.basedata
        self.add_button = add_button
        self.remove_button = remove_button
        self.output = None
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
        self.param_group.setVisible(False)

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

    def detailed_market_label(self, market, show_change=False):
        typ = market[f'betriebstyp_{self.suffix}']
        osm = ' OSM' if market.is_osm else ''
        kette = market.kette if market.kette != 'nicht aufgeführt' \
            else 'Anbieter unbekannt'
        label = (f'{market.name}{osm} ({market.id}) - {typ} ({kette})')
        if (show_change and
            market.id_betriebstyp_nullfall != market.id_betriebstyp_planfall):
            betriebstyp = 'Schließung' if market.id_betriebstyp_planfall == 0 \
                else market.betriebstyp_planfall
            label += f' geplant: {betriebstyp}'
        return label

    def fill_combo(self, select=None):
        self.combobox.blockSignals(True)
        self.combobox.clear()
        self.combobox.addItem('nichts ausgewählt')
        idx = 0
        markets = [m for m in self.markets.filter(**self.filter_args)]
        markets_sorted = sorted(markets, key=lambda m: m.AGS or ' ')
        for i, market in enumerate(markets_sorted):
            self.combobox.addItem(self.detailed_market_label(
                market, show_change=self.show_change), market)
            if select and market.id == select.id:
                idx = i + 1
        if idx:
            self.combobox.setCurrentIndex(idx)
        self.combobox.blockSignals(False)
        self.toggle_market(self.combobox.currentData())

    def select_market(self, feature):
        if not self.output or not self.output.layer:
            return
        self.output.layer.removeSelection()
        self.output.layer.select(feature.id())
        fid = feature.id()
        for idx in range(len(self.combobox)):
            market = self.combobox.itemData(idx)
            if market and fid == market.id:
                break
        self.combobox.setCurrentIndex(idx)

    def toggle_market(self, market, center_on_point=False):
        if market and self.output and self.output.layer:
            self.output.layer.removeSelection()
            self.output.layer.select(market.id)
            if center_on_point:
                center_canvas(self.canvas, market.geom.asPoint(),
                              self.output.layer.crs())
        self.setup_params(market)

    def setup_params(self, market):
        raise NotImplementedError

    def add_layer(self, zoom_to=False):
        self.output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        self.output.draw(
            label=self.market_label,
            style_file=self.layer_style,
            filter=self.layer_filter
        )
        self.select_tool.set_layer(self.output.layer)
        if zoom_to:
            self.output.zoom_to()

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
            self.changed.emit()

    def remove_markets(self):
        reply = QMessageBox.question(
            self.param_group, f'{self.market_label} löschen',
            f'Möchten Sie alle {self.market_label} löschen?',
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.markets.filter(**self.filter_args).delete()
            self.canvas.refreshAllLayers()
            self.fill_combo()
            self.changed.emit()

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
            self.param_group.setVisible(False)
            return
        self.param_group.setVisible(True)
        self.params = Params(layout, help_file='standortkonkurrenz_bestand.txt')
        self.params.name = Param(
            market.name, LineEdit(width=300),
            label='Name')

        self.params.add(Seperator(margin=0))

        # 'nicht aufgeführt' (kette 0) is first, rest alphabetical order
        ketten = sorted(self.ketten, key=lambda k: k.name.lower()
                        if k.name != 'nicht aufgeführt' else '')
        chain_ids = [typ.id_kette for typ in ketten]
        chain_labels = [kette.name for kette in ketten]
        chain_combo = ComboBox(chain_labels, data=chain_ids, width=300)
        value = self.ketten.get(id_kette=market.id_kette).name

        self.params.kette = Param(value, chain_combo, label='Anbieter')

        type_ids = [typ.id_betriebstyp for typ in self.typen]
        type_labels = [self.detailed_type_label(i) for i in type_ids if i > 0]
        type_combo = ComboBox(type_labels, data=type_ids, width=300)

        self.params.typ = Param(
            self.detailed_type_label(market.id_betriebstyp_nullfall),
            type_combo, label='Betriebstyp im Nullfall',
            value_label=market.betriebstyp_nullfall
        )

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
            self.changed.emit()

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
        self.changed.emit()
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
            self.param_group.setVisible(False)
            return
        self.param_group.setVisible(True)
        self.params = Params(
            layout, help_file='standortkonkurrenz_geplante_maerkte.txt')

        self.params.name = Param(
            market.name, LineEdit(width=300),
            label='Name')

        self.params.add(Seperator(margin=0))

        # 'nicht aufgeführt' (kette 0) is first, rest alphabetical order
        ketten = sorted(self.ketten, key=lambda k: k.name
                        if k.name != 'nicht aufgeführt' else '')
        chain_ids = [typ.id_kette for typ in ketten]
        chain_labels = [kette.name for kette in ketten]
        chain_combo = ComboBox(chain_labels, data=chain_ids, width=300)
        value = self.ketten.get(id_kette=market.id_kette).name

        self.params.kette = Param(value, chain_combo, label='Anbieter')

        type_ids = [typ.id_betriebstyp for typ in self.typen]
        type_labels = [self.detailed_type_label(i) for i in type_ids if i > 0]
        type_combo = ComboBox(type_labels, data=type_ids, width=300)

        self.params.typ = Param(
            self.detailed_type_label(market.id_betriebstyp_planfall),
            type_combo, label='Betriebstyp im Planfall',
            value_label=market.betriebstyp_planfall
        )

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
            self.changed.emit()

        self.params.show(title='Neuen Markt im Planfall bearbeiten')
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
        self.changed.emit()
        self.canvas.refreshAllLayers()
        self.fill_combo(select=market)


class ChangeMarkets(EditMarkets):
    layer_filter = ('id_betriebstyp_nullfall != id_betriebstyp_planfall '
                    'and id_betriebstyp_nullfall > 0')
    layer_style = 'standortkonkurrenz_veraenderte_maerkte.qml'
    filter_args = {'id_betriebstyp_nullfall__gt': 0}
    market_label = 'veränderte Märkte im Bestand'
    suffix = 'nullfall'
    show_change = True

    def add_layer(self, zoom_to=False):
        super().add_layer(zoom_to=zoom_to)
        # additionally the nullfall layer is required to select from
        self.nullfall_output = ProjectLayer.from_table(
            self.markets.table, groupname=self.layer_group)
        nullfall_layer = self.nullfall_output.draw(
            label=EditNullfallMarkets.market_label,
            style_file=EditNullfallMarkets.layer_style,
            filter=EditNullfallMarkets.layer_filter
        )
        self.select_tool.set_layer(nullfall_layer)
        if zoom_to:
            self.nullfall_output.zoom_to()

    def setup_params(self, market):
        if self.params:
            self.params.close()
        layout = self.param_group.layout()
        clear_layout(layout)
        if not market:
            self.param_group.setVisible(False)
            return
        self.param_group.setVisible(True)
        self.params = Params(
            layout, help_file='standortkonkurrenz_veraenderte_maerkte.txt')
        self.params.name = Param(market.name, label='Name')

        self.params.add(Seperator(margin=0))

        self.params.kette = Param(market.kette, label='Anbieter')

        self.params.nullfall = Param(
            market.betriebstyp_nullfall,
            label='Betriebstyp im Nullfall',
        )
        closed_label = 'Markt geschlossen'

        type_ids = [typ.id_betriebstyp for typ in self.typen]
        type_labels = []
        for tid in type_ids:
            type_labels.append(closed_label if tid == 0
                               else self.detailed_type_label(tid))
        type_combo = ComboBox(type_labels, data=type_ids, width=300)

        typ = market.id_betriebstyp_planfall
        self.params.planfall = Param(
            closed_label if typ == 0 else self.detailed_type_label(typ),
            type_combo, label='Betriebstyp im Planfall',
            value_label=closed_label if typ == 0 else market.betriebstyp_planfall
        )

        close_check = Checkbox()
        self.params.gets_closed = Param(
            typ == 0, close_check, label='Markt im Planfall schließen'
        )
        self.params.gets_closed.hide_in_overview = True

        def closed_toggled(checked):
            if checked:
                type_combo.set_value(closed_label)
        close_check.changed.connect(closed_toggled)

        def type_changed(value):
            close_check.set_value(value == closed_label)
        type_combo.changed.connect(type_changed)

        def save():
            id_bt = type_combo.get_data()
            bt = self.typen.get(id_betriebstyp=id_bt).name
            market.id_betriebstyp_planfall = id_bt
            market.betriebstyp_planfall = bt
            market.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_combo(select=market)
            self.changed.emit()

        self.params.show(title='Markt im Planfall verändern')
        self.params.changed.connect(save)

    def remove_markets(self):
        reply = QMessageBox.question(
            self.param_group, f'Veränderungen zurücksetzen',
            'Möchten Sie alle Veränderungen der bestehenden Märkte '
            'zurücksetzen?',
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for market in self.markets.filter(**self.filter_args):
                market.id_betriebstyp_planfall = market.id_betriebstyp_nullfall
                market.betriebstyp_planfall = market.betriebstyp_nullfall
                market.save()
            self.canvas.refreshAllLayers()
            self.fill_combo()


class EditCenters:

    def __init__(self, ui, canvas, project, layer_group=''):
        self.ui = ui
        self.canvas = canvas
        self.project = project
        self.drawing_tool = None
        self.params = None
        self.output = None
        self.select_tool = None
        self.project = project
        self.layer_group = layer_group

    def setupUi(self):
        self.drawing_tool = PolygonMapTool(
            self.ui.draw_center_button, canvas=self.canvas)
        self.drawing_tool.drawn.connect(self.add_center)
        self.ui.draw_center_button.clicked.connect(self.add_layer)
        self.ui.centers_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_center(self.ui.centers_combo.currentData(),
                                           center_on_point=True)
        )
        self.select_tool = FeaturePicker(self.ui.select_center_button,
                                         canvas=self.canvas)
        self.select_tool.feature_picked.connect(self.select_center)
        self.ui.select_center_button.clicked.connect(lambda: self.add_layer())
        self.ui.center_parameter_group.setVisible(False)


    def load_content(self):
        self.centers = Centers.features()
        self.fill_combo()

    def fill_combo(self, select=None):
        self.ui.centers_combo.blockSignals(True)
        self.ui.centers_combo.clear()
        self.ui.centers_combo.addItem('nichts ausgewählt')
        idx = 0
        centers = self.centers.filter(nutzerdefiniert=1)
        for i, center in enumerate(centers):
            self.ui.centers_combo.addItem(center.name, center)
            if select and center.id == select.id:
                idx = i + 1
        if idx:
            self.ui.centers_combo.setCurrentIndex(idx)
        self.ui.centers_combo.blockSignals(False)
        self.toggle_center(self.ui.centers_combo.currentData())

    def add_center(self, geom):
        center = self.centers.add(
            nutzerdefiniert=1,
            name='unbenanntes Zentrum',
            geom=geom
        )
        self.canvas.refreshAllLayers()
        self.fill_combo(select=center)

    def toggle_center(self, center, center_on_point=False):
        if self.output and self.output.layer and center:
            self.output.layer.removeSelection()
            self.output.layer.select(center.id)
            if center_on_point:
                center_canvas(self.canvas, center.geom.centroid().asPoint(),
                              self.output.layer.crs())
        self.setup_params(center)

    def add_layer(self, zoom_to=True):
        self.output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.output.draw(
            label='Zentren',
            style_file='standortkonkurrenz_zentren.qml',
            filter='nutzerdefiniert=1'
        )
        self.select_tool.set_layer(self.output.layer)

    def setup_params(self, center):
        if self.params:
            self.params.close()
        layout = self.ui.center_parameter_group.layout()
        clear_layout(layout)
        if not center:
            self.ui.center_parameter_group.setVisible(False)
            return
        self.ui.center_parameter_group.setVisible(True)
        self.params = Params(
            layout, help_file='standortkonkurrenz_zentren.txt')
        self.params.name = Param(center.name, LineEdit(width=300), label='Name')

        def save():
            center.name = self.params.name.value
            center.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_combo(select=center)

        self.params.show(title='Zentrum bearbeiten')
        self.params.changed.connect(save)

        last_row = self.params.layout.children()[-1]
        button = QPushButton()
        icon_path = 'iconset_mob/20190619_iconset_mob_delete_1.png'
        icon = QIcon(os.path.join(self.project.settings.IMAGE_PATH, icon_path))
        button.setText('Zentrum entfernen')
        button.setIcon(icon)
        button.setToolTip(
            '<p><span style=" font-weight:600;">Zentrum entfernen</span>'
            '</p><p>Löscht das gewählte Zentrum. </p>')
        last_row.insertWidget(0, button)
        button.clicked.connect(lambda: self.remove_center(center))

    def remove_center(self, center):
        if not center:
            return
        reply = QMessageBox.question(
            self.ui, 'Zentrum entfernen',
            f'Soll das Zentrum "{center.name}" entfernt werden?\n',
             QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            center.delete()
            self.canvas.refreshAllLayers()
            self.fill_combo()

    def select_center(self, feature):
        if not self.output or not self.output.layer:
            return
        self.output.layer.removeSelection()
        self.output.layer.select(feature.id())
        fid = feature.id()
        for idx in range(len(self.ui.centers_combo)):
            center = self.ui.centers_combo.itemData(idx)
            if center and fid == center.id:
                break
        self.ui.centers_combo.setCurrentIndex(idx)

    def close(self):
        if self.drawing_tool:
            self.drawing_tool.set_active(False)
        if self.select_tool:
            self.select_tool.set_active(False)
        if self.params:
            self.params.close()


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
            lambda: self.show_markets_and_centers(zoom_to=True))

        self.ui.add_osm_button.clicked.connect(self.read_osm)
        self.ui.remove_osm_button.clicked.connect(self.remove_osm)

        self.nullfall_edit = EditNullfallMarkets(
            self.ui.nullfall_market_combo,
            self.ui.select_nullfall_market_button,
            self.ui.nullfall_market_parameter_group,
            self.canvas,
            self.project,
            remove_button=self.ui.remove_nullfall_markets_button,
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
            self.canvas, self.project,
            remove_button=self.ui.reset_changed_markets_button
        )
        self.changed_edit.setupUi()
        self.nullfall_edit.changed.connect(self.changed_edit.fill_combo)

        self.center_edit = EditCenters(self.ui, self.canvas, self.project,
                                      layer_group=self.layer_group)
        self.center_edit.setupUi()

        self.ui.calculate_button.clicked.connect(self.calculate)
        self.ui.osm_buffer_input.setEnabled(False)
        self.ui.osm_buffer_slider.setEnabled(False)

        self.ui.template_help_button.clicked.connect(self.show_template_help)
        manual_path = os.path.join(
            self.settings.HELP_PATH,
            'Anleitung_Standortkonkurrenz_Supermaerkte.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(manual_path))

    def load_content(self):
        self.centers = Centers.features()
        if len(self.centers.filter(nutzerdefiniert=0)) == 0:
            QMessageBox.warning(
                self.ui, 'Hinweis',
                'Das Projekt wurde scheinbar mit einer alten '
                'Projekt-Check-Version erstellt. Bitte legen Sie eine neues '
                'Projekt an, um die Standortkonkurrenz dort nutzen zu können.')
        self.markets = Markets.features(create=True)
        self.relations = MarketCellRelations.features(create=True)
        self.nullfall_edit.load_content()
        self.planfall_edit.load_content()
        self.changed_edit.load_content()
        self.center_edit.load_content()

    def show_template_help(self):
        types = MarketTemplate.template_types.keys()
        typ, ok = QInputDialog.getItem(
            self.ui, 'Ausfüllhilfe anzeigen',
            'Dateiformat', types, 0, False)
        if ok:
            fn = os.path.join(self.settings.HELP_PATH,
                              MarketTemplate.template_types[typ][1])
            open_file(fn)

    def show_markets_and_centers(self, zoom_to=True):
        self.planfall_edit.add_layer()
        self.changed_edit.add_layer()
        self.nullfall_edit.add_layer(zoom_to=zoom_to)
        self.center_edit.add_layer()

    def show_communities(self, zoom_to=True):
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.communities_selected_layer = output.draw(
            label='Ausgewählte Gemeinden im Betrachtungsraum',
            style_file='standortkonkurrenz_gemeinden_ausgewaehlt.qml',
            filter='auswahl!=0 AND nutzerdefiniert=-1'
        )
        self.community_picker.set_layer(self.communities_selected_layer)

        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.communities_not_selected_layer = output.draw(
            label='Nicht ausgewählte Gemeinden',
            style_file='standortkonkurrenz_gemeinden_nicht_ausgewaehlt.qml',
            filter='auswahl=0 AND nutzerdefiniert=-1'
        )
        self.community_picker.add_layer(self.communities_not_selected_layer)
        if zoom_to:
            output.zoom_to()

    def community_picked(self, feature):
        center = self.centers.get(id=feature.id())
        # -1 indicates the project community, deselection not allowed
        if center.auswahl == -1:
            return
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
                self.nullfall_edit.fill_combo()
                self.nullfall_edit.add_layer(zoom_to=True)
                self.changed_edit.fill_combo()
            job = MarketTemplateImportWorker(path, self.project,
                                             epsg=self.settings.EPSG)
            dialog = ProgressDialog(job, parent=self.ui, on_success=on_success)
            dialog.show()

    def read_osm(self):
        buffer = self.ui.osm_buffer_input.value() \
            if self.ui.osm_buffer_check.isChecked() else 0
        job = ReadOSMWorker(self.project, epsg=self.settings.EPSG,
                            buffer=buffer, truncate=False)
        def on_success(r):
            self.nullfall_edit.fill_combo()
            self.nullfall_edit.add_layer(zoom_to=True)
            self.changed_edit.fill_combo()
        dialog = ProgressDialog( job, parent=self.ui, on_success=on_success)
        dialog.show()

    def remove_osm(self):
        reply = QMessageBox.question(
            self.ui, 'OSM-Märkte löschen',
            f'Möchten Sie alle OSM-Märkte löschen?',
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.markets.filter(is_osm=True).delete()
            self.nullfall_edit.fill_combo()
            self.changed_edit.fill_combo()
            self.canvas.refreshAllLayers()
            self.markets.filter()

    def calculate(self):
        job = Projektwirkung(self.project, recalculate=False)
        success, msg = job.validate_inputs()
        if not success:
            QMessageBox.warning(self.ui, 'Fehler', msg)
            return

        def on_success(r):
            self.show_results()

        dialog = ProgressDialog(job, parent=self.ui, on_success=on_success)
        dialog.show()

    def show_results(self):
        planfall_markets = self.markets.filter(id_betriebstyp_planfall__gt=0)
        for market in planfall_markets:
            if market.id_betriebstyp_nullfall == market.id_betriebstyp_planfall:
                continue
            output = ProjectLayer.from_table(
                self.relations.table, groupname=self.layer_group)
            layer_name = f'Kaufkraftbindung {market.name} ({market.id})'
            output.draw(
                label=layer_name,
                style_file='standortkonkurrenz_kk_bindung.qml',
                filter=f'id_markt={market.id}',
                expanded=False
            )
        self.markets.filter()

        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Umsatzveränderung Bestand Zentren',
            style_file='standortkonkurrenz_umsatzveraenderung_zentren.qml',
            filter='nutzerdefiniert=1',
            expanded=False
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Umsatzveränderung Bestand Verwaltungsgemeinschaften',
            style_file='standortkonkurrenz_umsatzveraenderung_vwg.qml',
            filter='nutzerdefiniert=-1',
            expanded=False
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Zentralität Nullfall',
            style_file='standortkonkurrenz_zentralitaet_nullfall.qml',
            filter='nutzerdefiniert=0 and auswahl=1',
            expanded=False
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Zentralität Planfall',
            style_file='standortkonkurrenz_zentralitaet_planfall.qml',
            filter='nutzerdefiniert=0 and auswahl=1',
            expanded=False
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Entwicklung Zentralität',
            style_file='standortkonkurrenz_entwicklung_zentralitaet.qml',
            filter='nutzerdefiniert=0 and auswahl=1',
            expanded=False
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Verkaufsflächendichte Nullfall',
            style_file='standortkonkurrenz_verkaufsflaechendichte_nullfall.qml',
            filter='nutzerdefiniert=0 and auswahl=1',
            expanded=False
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Verkaufsflächendichte Planfall',
            style_file='standortkonkurrenz_verkaufsflaechendichte_planfall.qml',
            filter='nutzerdefiniert=0 and auswahl=1',
            expanded=False
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        output.draw(
            label='Entwicklung Verkaufsflächendichte',
            style_file='standortkonkurrenz_entwicklung_'
            'verkaufsflaechendichte.qml',
            filter='nutzerdefiniert=0 and auswahl=1',
            expanded=False
        )

    def close(self):
        self.community_picker.set_active(False)
        self.nullfall_edit.close()
        self.planfall_edit.close()
        self.changed_edit.close()
        self.center_edit.close()
        super().close()

