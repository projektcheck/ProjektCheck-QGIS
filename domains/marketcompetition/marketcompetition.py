# -*- coding: utf-8 -*-
'''
***************************************************************************
    marketcompetition.py
    ---------------------
    Date                 : July 2019
    Copyright            : (C) 2019 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

domain for the definition of the market-distribution in the study area and
defining scenarios to analyse the change of market income
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

from qgis.PyQt.QtWidgets import (QFileDialog, QMessageBox, QInputDialog,
                                 QCheckBox, QPushButton)
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
import os

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.base.tools import (FeaturePicker, MapClickedTool,
                                     PolygonMapTool)
from projektcheck.base.dialogs import ProgressDialog
from projektcheck.base.params import Params, Param, Seperator
from projektcheck.base.inputs import LineEdit, ComboBox, Checkbox
from projektcheck.utils.utils import (center_canvas, clear_layout,
                                      get_ags, open_file)
from .tables import Centers, Markets, MarketCellRelations
from .read_osm import ReadOSMWorker
from .market_templates import (MarketTemplateCreateDialog, MarketTemplate,
                               MarketTemplateImportWorker)
from .projektwirkung import Projektwirkung


class EditMarkets(QObject):
    '''
    abstract class for setting markets on the map, setting up their parameters
    to edit their properties and to visualize them on the map
    '''
    # QGIS layer filter
    layer_filter = ''
    # style for output layer
    layer_style = ''
    # backend feature filter
    filter_args = {}
    # label for market type
    market_label = ''
    # 'nullfall' or 'planfall'
    suffix = ''
    # show type change from status quo to scenario
    show_change = False
    # emitted when the market data is changed
    changed = pyqtSignal()

    def __init__(self, combobox, select_button, param_group, canvas, project,
                 add_button=None, remove_button=None, layer_group=''):
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
        self.layer_group = layer_group
        # just used for calculating the vkfl
        self.market_tool = ReadOSMWorker(self.project)

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

    def detailed_type_label(self, id_betriebstyp) -> str:
        '''
        pretty label for a type of business
        '''
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

    def detailed_market_label(self, market, show_change=False) -> str:
        '''
        pretty label for a market
        '''
        typ = market[f'betriebstyp_{self.suffix}']
        osm = ' OSM' if market.is_osm else ''
        kette = market.kette if market.kette != 'nicht aufgeführt' \
            else 'Anbieter unbekannt'
        label = (f'{market.name}{osm} ({market.id}) - {typ} ({kette})')
        if (show_change and
            market.id_betriebstyp_nullfall != market.id_betriebstyp_planfall):
            betriebstyp = 'Schließung' if market.id_betriebstyp_planfall == 0 \
                else market.betriebstyp_planfall
            label = f'-> {label} geplant: {betriebstyp}'
        return label

    def fill_combo(self, select: 'Feature' = None):
        '''
        fill combobox with available markets, preselect given market
        '''
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
        '''
        select and highlight given market
        '''
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
        '''
        set up given market
        '''
        if market and self.output and self.output.layer:
            self.output.layer.removeSelection()
            self.output.layer.select(market.id)
            if center_on_point:
                center_canvas(self.canvas, market.geom.asPoint(),
                              self.output.layer.crs())
        self.setup_params(market)

    def setup_params(self, market):
        '''
        override to set up parameters for given market
        '''
        raise NotImplementedError

    def add_layer(self, zoom_to=False):
        '''
        add output layer showing markets
        '''
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
        '''
        override to add a market with given geometry (point) to the database
        '''
        raise NotImplementedError

    def remove_market(self, market):
        '''
        remove given market from database
        '''
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
        '''
        remove all markets (filtered by self.filter_args) except the
        automatically created ones
        '''
        reply = QMessageBox.question(
            self.param_group, f'{self.market_label} löschen',
            f'Möchten Sie alle {self.market_label} löschen?',
            QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # markets on project area can never be deleted
            self.markets.filter(id_teilflaeche=-1, **self.filter_args).delete()
            self.canvas.refreshAllLayers()
            self.fill_combo()
            self.changed.emit()

    def close(self):
        '''
        deactivate drawing tool and close parameters
        '''
        if self.add_market_tool:
            self.add_market_tool.set_active(False)
        if self.params:
            self.params.close()


class EditNullfallMarkets(EditMarkets):
    '''
    nullfall (status quo) market control
    '''
    layer_filter = 'id_betriebstyp_nullfall > 0'
    layer_style = 'standortkonkurrenz_maerkte_im_bestand.qml'
    filter_args = {'id_betriebstyp_nullfall__gt': 0}
    market_label = 'Märkte im Bestand'
    suffix = 'nullfall'

    def setup_params(self, market):
        '''
        set up the parameters to edit the given status quo market
        '''
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
            vkfl = self.market_tool.betriebstyp_to_vkfl(
                market.id_betriebstyp_nullfall, market.id_kette)
            market.vkfl = vkfl
            market.vkfl_planfall = vkfl
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
        '''
        add a status quo market to the database
        '''
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
        vkfl = self.market_tool.betriebstyp_to_vkfl(
            market.id_betriebstyp_nullfall, market.id_kette)
        market.vkfl = vkfl
        market.vkfl_planfall = vkfl
        crs = QgsCoordinateReferenceSystem(f'EPSG:{self.project.settings.EPSG}')
        ags = get_ags([market], self.basedata, source_crs=crs)[0]
        market.AGS = ags.AGS
        market.save()
        self.changed.emit()
        # workaround: if layer had no data before it needs to be readded to show
        # sth, refresh doesn't work
        if len(self.markets) == 1:
            self.add_layer()
        self.canvas.refreshAllLayers()
        self.fill_combo(select=market)


class EditPlanfallMarkets(EditMarkets):
    '''
    planfall (scenario) market control
    '''
    layer_filter = 'id_betriebstyp_nullfall = 0'
    layer_style = 'standortkonkurrenz_geplante_maerkte.qml'
    filter_args = {'id_betriebstyp_nullfall': 0}
    market_label = 'geplante Märkte'
    suffix = 'planfall'

    def setup_params(self, market):
        '''
        set up the parameters to edit the given scenario market
        '''
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

        self.params.name = Param(market.name, LineEdit(width=300),
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
            self.detailed_type_label(market.id_betriebstyp_planfall),
            type_combo, label='Neue Märkte',
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
            vkfl = self.market_tool.betriebstyp_to_vkfl(
                market.id_betriebstyp_planfall, market.id_kette)
            market.vkfl_planfall = vkfl
            market.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_combo(select=market)
            self.changed.emit()

        self.params.show(title='Neuen Markt im Planfall bearbeiten')
        self.params.changed.connect(save)

        # markets on project areas can not be deleted
        if market.id_teilflaeche < 0:
            last_row = self.params.layout.children()[-1]
            button = QPushButton()
            icon_path = 'iconset_mob/20190619_iconset_mob_delete_1.png'
            icon = QIcon(os.path.join(self.project.settings.IMAGE_PATH,
                                      icon_path))
            button.setText('Markt entfernen')
            button.setIcon(icon)
            button.setToolTip(
                '<p><span style=" font-weight:600;">Markt entfernen</span>'
                '</p><p>Löscht den aktuell gewählten Markt. '
                '<br/>Dieser Schritt kann nicht rückgängig gemacht '
                'werden. </p>')
            last_row.insertWidget(0, button)
            button.clicked.connect(lambda: self.remove_market(market))

    def add_market(self, geom, name='unbenannter geplanter Markt'):
        '''
        add a scenario market to the database
        '''
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
        market.AGS = ags.AGS
        vkfl = self.market_tool.betriebstyp_to_vkfl(
            market.id_betriebstyp_planfall, market.id_kette)
        market.vkfl_planfall = vkfl
        market.save()
        self.changed.emit()
        # workaround: if layer had no data before it needs to be readded to show
        # sth, refresh doesn't work
        if len(self.markets) == 1:
            self.add_layer()
        self.canvas.refreshAllLayers()
        self.fill_combo(select=market)


class ChangeMarkets(EditMarkets):
    '''
    control markets already existing in status quo but are changed in the
    scenario
    '''
    layer_filter = ('id_betriebstyp_nullfall != id_betriebstyp_planfall '
                    'and id_betriebstyp_nullfall > 0')
    layer_style = 'standortkonkurrenz_veraenderte_maerkte.qml'
    filter_args = {'id_betriebstyp_nullfall__gt': 0}
    market_label = 'Veränderte Märkte im Bestand'
    suffix = 'nullfall'
    show_change = True

    def __init__(self, nullfall_edit, combobox, select_button, param_group,
                 canvas, project, remove_button=None, layer_group=''):
        super().__init__(combobox, select_button, param_group,
                         canvas, project, remove_button=remove_button,
                         layer_group=layer_group)
        self.nullfall_edit = nullfall_edit

    def add_layer(self, zoom_to=False):
        '''
        add the nullfall layer in addition to layer showing the changed markets
        '''
        super().add_layer(zoom_to=zoom_to)
        self.nullfall_edit.add_layer(zoom_to)
        self.select_tool.set_layer(self.nullfall_edit.output.layer)

    def setup_params(self, market):
        '''
        set up the parameters to change attributes of the given status quo
        market in the scenario
        '''

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
            vkfl = self.market_tool.betriebstyp_to_vkfl(
                market.id_betriebstyp_planfall, market.id_kette)
            market.vkfl_planfall = vkfl
            market.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_combo(select=market)
            self.changed.emit()

        self.params.show(title='Markt im Planfall verändern')
        self.params.changed.connect(save)

    def remove_markets(self):
        '''
        reset all changes made to status quo markets in the scenario
        '''
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
    '''
    controls centers drawn by users, centers will be evaluated seperately during
    the calculation of the "Projektwirkung"
    '''
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
        '''
        fill the center combobox with all drawn centers
        '''
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
        '''
        add a new center with default name and given geometry
        '''
        center = self.centers.add(
            nutzerdefiniert=1,
            name='unbenanntes Zentrum',
            geom=geom
        )
        self.canvas.refreshAllLayers()
        self.fill_combo(select=center)

    def toggle_center(self, center, center_on_point=False):
        '''
        change active center
        '''
        if self.output and self.output.layer and center:
            self.output.layer.removeSelection()
            self.output.layer.select(center.id)
            if center_on_point:
                center_canvas(self.canvas, center.geom.centroid().asPoint(),
                              self.output.layer.crs())
        self.setup_params(center)

    def add_layer(self, zoom_to=True):
        '''
        show the centers in a layer
        '''
        self.output = ProjectLayer.from_table(
            self.centers.table, groupname=self.layer_group)
        self.output.draw(
            label='Zentren',
            style_file='standortkonkurrenz_zentren.qml',
            filter='nutzerdefiniert=1'
        )
        self.select_tool.set_layer(self.output.layer)

    def setup_params(self, center):
        '''
        set up the parameters to edit the given center
        '''
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
        '''
        remove the given center from the database
        '''
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
        '''
        select and highlight given center
        '''
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
        '''
        close tools and parameters
        '''
        if self.drawing_tool:
            self.drawing_tool.set_active(False)
        if self.select_tool:
            self.select_tool.set_active(False)
        if self.params:
            self.params.close()


class SupermarketsCompetition(Domain):
    '''
    domain-widget for planning new markets/changes to existing markets in the
    study area and calculating the impact on the status quo
    '''

    ui_label = 'Standortkonkurrenz Supermärkte'
    ui_file = 'domain_08-SKSM.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_supermarkets_1.png"

    layer_group = 'Wirkungsbereich 7 - Standortkonkurrenz Supermärkte'
    nullfall_group = 'Märkte im Nullfall'
    planfall_group = 'Märkte im Planfall'
    study_group = 'Betrachtungsraum'
    results_group = 'Projektwirkung'

    def setupUi(self):
        self.community_picker = FeaturePicker(self.ui.select_communities_button,
                                              canvas=self.canvas)
        self.community_picker.feature_picked.connect(self.add_to_study_area)

        self.ui.create_template_button.clicked.connect(
            lambda: MarketTemplateCreateDialog().show())
        self.ui.read_template_button.clicked.connect(self.read_template)
        self.ui.select_communities_button.clicked.connect(
            lambda: self.show_study_area(
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
            add_button=self.ui.add_nullfall_market_button,
            layer_group=f'{self.layer_group}/{self.nullfall_group}'
        )
        self.nullfall_edit.setupUi()
        self.nullfall_edit.changed.connect(self.remove_results)

        self.planfall_edit = EditPlanfallMarkets(
            self.ui.planfall_market_combo,
            self.ui.select_planfall_market_button,
            self.ui.planfall_market_parameter_group,
            self.canvas, self.project,
            remove_button=self.ui.remove_planfall_markets_button,
            add_button=self.ui.add_planfall_market_button,
            layer_group=f'{self.layer_group}/{self.planfall_group}'
        )
        self.planfall_edit.setupUi()
        self.planfall_edit.changed.connect(self.remove_results)

        self.changed_edit = ChangeMarkets(
            self.nullfall_edit,
            self.ui.changed_market_combo,
            self.ui.select_changed_market_button,
            self.ui.changed_market_parameter_group,
            self.canvas, self.project,
            remove_button=self.ui.reset_changed_markets_button,
            layer_group=f'{self.layer_group}/{self.planfall_group}'
        )
        self.changed_edit.setupUi()
        self.nullfall_edit.changed.connect(self.changed_edit.fill_combo)
        self.changed_edit.changed.connect(self.remove_results)

        self.center_edit = EditCenters(
            self.ui, self.canvas, self.project,
            layer_group=f'{self.layer_group}/{self.study_group}')
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
        super().load_content()
        # add layer-groups in specific order
        for group_name in [self.nullfall_group, self.planfall_group,
                           self.results_group, self.study_group]:
            ProjectLayer.add_group(f'{self.layer_group}/{group_name}',
                                   prepend=False)

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
        '''
        let the user select a template type in a dialog and show the associated
        pdf help file
        '''
        types = MarketTemplate.template_types.keys()
        typ, ok = QInputDialog.getItem(
            self.ui, 'Ausfüllhilfe anzeigen',
            'Dateiformat', types, 0, False)
        if ok:
            fn = os.path.join(self.settings.HELP_PATH,
                              MarketTemplate.template_types[typ][1])
            open_file(fn)

    def show_markets_and_centers(self, zoom_to=True):
        '''
        add layers of markets in status quo and scenario and the user-defined
        centers
        '''
        self.planfall_edit.add_layer()
        self.changed_edit.add_layer()
        self.nullfall_edit.add_layer(zoom_to=zoom_to)
        self.center_edit.add_layer()

    def show_study_area(self, zoom_to=True):
        '''
        add layers with communities selectable to be in the study area
        '''
        group_name = f'{self.layer_group}/{self.study_group}'
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        self.communities_selected_layer = output.draw(
            label='Ausgewählte Gemeinden/Verw.gemeinschaften im '
            'Betrachtungsraum',
            style_file='standortkonkurrenz_gemeinden_ausgewaehlt.qml',
            filter='auswahl!=0 AND nutzerdefiniert=-1'
        )
        self.community_picker.set_layer(self.communities_selected_layer)

        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        self.communities_not_selected_layer = output.draw(
            label='Nicht ausgewählte Gemeinden/Verw.gemeinschaften',
            style_file='standortkonkurrenz_gemeinden_nicht_ausgewaehlt.qml',
            filter='auswahl=0 AND nutzerdefiniert=-1'
        )
        self.community_picker.add_layer(self.communities_not_selected_layer)
        if zoom_to:
            output.zoom_to()

    def add_to_study_area(self, community):
        '''
        add given community to the study area
        '''
        center = self.centers.get(id=community.id())
        # -1 indicates the project community, deselection not allowed
        if center.auswahl == -1:
            return
        center.auswahl = not center.auswahl
        center.save()
        self.remove_results()
        self.canvas.refreshAllLayers()

    def read_template(self):
        '''
        let the user select a template and load its entries to the status quo
        markets
        '''
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
                self.remove_results()
            job = MarketTemplateImportWorker(path, self.project,
                                             epsg=self.settings.EPSG)
            dialog = ProgressDialog(job, parent=self.ui, on_success=on_success)
            dialog.show()

    def read_osm(self):
        '''
        query geoserver for markets in the study area and add them to the
        status quo markets
        '''
        buffer = self.ui.osm_buffer_input.value() \
            if self.ui.osm_buffer_check.isChecked() else 0
        job = ReadOSMWorker(self.project, epsg=self.settings.EPSG,
                            buffer=buffer, truncate=False)
        def on_success(r):
            self.nullfall_edit.fill_combo()
            self.nullfall_edit.add_layer(zoom_to=True)
            self.changed_edit.fill_combo()
            self.remove_results()
        dialog = ProgressDialog( job, parent=self.ui, on_success=on_success)
        dialog.show()

    def remove_osm(self):
        '''
        remove all markets that were added by a query of the geoserver
        '''
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
            self.remove_results()

    def calculate(self):
        '''
        calculate the impact of the changes to status quo and show the results
        as layers
        '''
        job = Projektwirkung(self.project, recalculate=False)
        success, msg = job.validate_inputs()
        if not success:
            QMessageBox.warning(self.ui, 'Fehler', msg)
            return
        self.remove_results()

        def on_success(r):
            self.show_results()
            if not self.settings.show_result_layer_info:
                return
            msg_box = QMessageBox(self.ui)
            msg_box.setText('Die Ergebnislayer wurden dem QGIS-Layerbaum '
                            'in der Gruppe "Projektwirkung" hinzugefügt. Nur der'
                            ' oberste Ergebnislayer ist aktiviert.\n\n'
                            'Um die anderen Ergebnisse anzuzeigen, '
                            'aktivieren Sie sie bitte manuell im Layerbaum.\n')
            check = QCheckBox('nicht wieder anzeigen')
            msg_box.setCheckBox(check)
            msg_box.exec()
            if check.isChecked():
                self.settings.show_result_layer_info = False

        dialog = ProgressDialog(job, parent=self.ui, on_success=on_success)
        dialog.show()

    def show_results(self):
        '''
        show the results from "Projektwirkung" as layers
        '''
        # hide layers messing up the readability of the results
        study_output = ProjectLayer.find(self.study_group)
        if study_output:
            study_output[0].setItemVisibilityChecked(False)
        nullfall_output = ProjectLayer.find(self.nullfall_group)
        if nullfall_output:
            nullfall_output[0].setItemVisibilityChecked(False)

        group_name = f'{self.layer_group}/{self.results_group}'
        planfall_markets = self.markets.filter(id_betriebstyp_planfall__gt=0)
        # check first one only
        checked = True
        for market in planfall_markets:
            if market.id_betriebstyp_nullfall == market.id_betriebstyp_planfall:
                continue
            output = ProjectLayer.from_table(
                self.relations.table, groupname=group_name)
            layer_name = f'Kaufkraftbindung {market.name} ({market.id})'
            output.draw(
                label=layer_name,
                style_file='standortkonkurrenz_kk_bindung_2.qml',
                filter=f'id_markt={market.id}',
                expanded=False, checked=checked
            )
            # zoom to first layer
            if checked:
                output.zoom_to()
            checked = False
        self.markets.filter()

        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Umsatzveränderung der Bestandsmärke nach Zentren',
            style_file='standortkonkurrenz_umsatzveraenderung_zentren.qml',
            filter='nutzerdefiniert=1',
            expanded=False, checked=checked
        )
        checked = False
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Umsatzveränderung der Bestandsmärke nach Gemeinde/Verw-Gem.',
            style_file='standortkonkurrenz_umsatzveraenderung_vwg.qml',
            filter='nutzerdefiniert=-1 and auswahl!=0',
            expanded=False, checked=checked
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Zentralität im Nullfall nach Gemeinde/Verw-Gem.',
            style_file='standortkonkurrenz_zentralitaet_nullfall.qml',
            filter='nutzerdefiniert=-1 and auswahl!=0',
            expanded=False, checked=checked
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Zentralität im Planfall nach Gemeinde/Verw-Gem.',
            style_file='standortkonkurrenz_zentralitaet_planfall.qml',
            filter='nutzerdefiniert=-1 and auswahl!=0',
            expanded=False, checked=checked
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Veränderung der Zentralität im Planfall gegenüber Nullfall',
            style_file='standortkonkurrenz_entwicklung_zentralitaet.qml',
            filter='nutzerdefiniert=-1 and auswahl!=0',
            expanded=False, checked=checked
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Verkaufsflächendichte im Nullfall',
            style_file='standortkonkurrenz_verkaufsflaechendichte_nullfall.qml',
            filter='nutzerdefiniert=-1 and auswahl!=0',
            expanded=False, checked=checked
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Verkaufsflächendichte im Planfall',
            style_file='standortkonkurrenz_verkaufsflaechendichte_planfall.qml',
            filter='nutzerdefiniert=-1 and auswahl!=0',
            expanded=False, checked=checked
        )
        output = ProjectLayer.from_table(
            self.centers.table, groupname=group_name)
        output.draw(
            label='Veränderung der Verkaufsflächendichte im Planfall '
            'gegenüber Nullfall',
            style_file='standortkonkurrenz_entwicklung_'
            'verkaufsflaechendichte.qml',
            filter='nutzerdefiniert=-1 and auswahl!=0',
            expanded=False, checked=checked
        )

    @classmethod
    def remove_results(cls):
        '''
        remove result layers
        '''
        # ToDo: remove results from database (?)
        group = ProjectLayer.find(cls.results_group,
                                  groupname=cls.layer_group)
        if group:
            group[0].removeAllChildren()

    def close(self):
        '''
        close tools and parameters
        '''
        self.community_picker.set_active(False)
        self.nullfall_edit.close()
        self.planfall_edit.close()
        self.changed_edit.close()
        self.center_edit.close()
        super().close()

