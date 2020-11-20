# -*- coding: utf-8 -*-
'''
***************************************************************************
    traffic.py
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

domain for calculating and visualizing the additional traffic load caused by
the project areas
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

from qgis.PyQt.QtWidgets import QMessageBox, QPushButton
from qgis.PyQt.QtGui import QIcon
import os
import numpy as np

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.base.dialogs import ProgressDialog
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.traffic.tables import (
    TrafficLoadLinks, Itineraries, TransferNodes, Ways, Connectors, RouteLinks)
from projektcheck.domains.traffic.routing import (Routing,
                                                  TransferNodeCalculation)
from projektcheck.base.params import (Params, Param, Title,
                                      Seperator, SumDependency)
from projektcheck.base.inputs import SpinBox, Slider, LineEdit
from projektcheck.domains.constants import Nutzungsart
from projektcheck.utils.utils import open_file, center_canvas, clear_layout
from projektcheck.base.tools import (FeaturePicker, MapClickedTool,
                                     FeatureDragger)


class Traffic(Domain):
    '''
    domain-widget for calculating and visualizing the additional traffic load
    '''

    ui_label = 'Verkehr im Umfeld'
    ui_file = 'domain_03-ViU.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_traffic_6.png"

    layer_group = "Wirkungsbereich 3 - Verkehr im Umfeld"

    @classmethod
    def reset(cls, project=None):
        '''
        remove existing results
        '''
        if not project:
            project = cls.project_manager.active_project
        RouteLinks.features(project=project, create=True).table.truncate()
        Itineraries.features(project=project, create=True).table.truncate()
        TrafficLoadLinks.features(project=project, create=True).table.truncate()
        Ways.features(project=project, create=True).table.truncate()

    def setupUi(self):
        self.node_output = None
        self.itinerary_output = None
        self.ways_params = None
        self.weight_params = None
        self.node_params = None
        self.select_tool = FeaturePicker(self.ui.select_transfer_node_button,
                                         canvas=self.canvas)
        self.select_tool.feature_picked.connect(self.select_node)

        self.drag_tool = FeatureDragger(
            self.ui.move_transfer_node_button, canvas=self.canvas)
        self.drag_tool.feature_dragged.connect(self.move_node)

        self.ui.select_transfer_node_button.clicked.connect(
            lambda: self.draw_nodes())
        self.ui.move_transfer_node_button.clicked.connect(
            lambda: self.draw_nodes())

        self.ui.transfer_node_combo.currentIndexChanged.connect(
            lambda idx: self.toggle_node(
                self.ui.transfer_node_combo.currentData(), center_on_point=True)
        )
        self.ui.transfer_node_parameter_group.setVisible(False)

        self.add_node_tool = MapClickedTool(
            self.ui.add_transfer_node_button, canvas=self.canvas,
            target_epsg=self.project.settings.EPSG)
        self.add_node_tool.map_clicked.connect(self.add_node)
        self.ui.add_transfer_node_button.clicked.connect(
            lambda: self.draw_nodes())

        self.ui.calc_transfer_nodes_button.clicked.connect(self.calculate_nodes)
        self.ui.calculate_traffic_button.clicked.connect(
            self.calculate_traffic)

        self.ui.remove_transfer_nodes_button.clicked.connect(self.remove_nodes)

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Verkehr_im_Umfeld.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

    def load_content(self):
        super().load_content()
        output = ProjectLayer.find('Projektdefinition')
        if output:
            output[0].setItemVisibilityChecked(True)
        self.areas = Teilflaechen.features(project=self.project)
        self.links = RouteLinks.features(project=self.project, create=True)
        self.traffic_load = TrafficLoadLinks.features(project=self.project,
                                                      create=True)
        self.transfer_nodes = TransferNodes.features(project=self.project,
                                                     create=True)
        self.itineraries = Itineraries.features(project=self.project,
                                                create=True)
        self.ways = Ways.features(project=self.project, create=True)
        self.connectors = Connectors.features(project=self.project, create=True)

        self.draw_nodes()
        self.fill_node_combo()
        self.setup_ways()
        self.setup_weights()

    def fill_node_combo(self, select: 'Feature' = None):
        '''
        set up node selection
        '''
        self.ui.transfer_node_combo.blockSignals(True)
        self.ui.transfer_node_combo.clear()
        self.ui.transfer_node_combo.addItem('nichts ausgewählt')
        idx = 0
        for i, node in enumerate(self.transfer_nodes):
            self.ui.transfer_node_combo.addItem(node.name, node)
            if select and node.id == select.id:
                idx = i + 1
        if idx:
            self.ui.transfer_node_combo.setCurrentIndex(idx)
        self.ui.transfer_node_combo.blockSignals(False)
        self.toggle_node(self.ui.transfer_node_combo.currentData())

    def toggle_node(self, node, center_on_point=False):
        '''
        set up given transfer node
        '''
        if node and self.node_output and self.node_output.layer:
            self.node_output.layer.removeSelection()
            self.node_output.layer.select(node.id)
            if center_on_point:
                center_canvas(self.canvas, node.geom.asPoint(),
                              self.node_output.layer.crs())
        self.setup_node_params(node)

    def add_node(self, geom, name=None):
        '''
        add a transfer node to the database
        '''
        if self.itinerary_output:
            self.itinerary_output.remove()
        # equal share of weight for new node
        weight = 100 / (len(self.transfer_nodes) + 1)
        # reduce weights of other nodes by weight of new node
        d = (100 - weight) / 100
        for node in self.transfer_nodes:
            node.weight = round(node.weight * d)
            node.save()
        # distribute delta caused by rounding errors
        weight = 100 - sum(self.transfer_nodes.values('weight'))
        node = self.transfer_nodes.add(
            name=name,
            geom=geom,
            weight=weight
        )
        if not name:
            node.name = f'Herkunfts-/Zielpunkt {node.id + 1}'
            node.save()
        # workaround: if layer had no data before it needs to be readded to show
        # sth, refresh doesn't work
        if len(self.transfer_nodes) == 1:
            self.draw_nodes()
        self.canvas.refreshAllLayers()
        self.fill_node_combo(select=node)
        self.links.table.truncate()
        self.traffic_load.table.truncate()
        self.setup_weights()

    def move_node(self, feature_id: int, point: 'QgsPointXY'):
        '''
        move transfer node with given id to given point
        '''
        node = self.transfer_nodes.get(id=feature_id)
        node.geom = point
        node.save()
        self.drag_tool.reset()
        self.canvas.refreshAllLayers()
        self.links.table.truncate()
        self.traffic_load.table.truncate()
        self.set_status()

    def select_node(self, feature):
        '''
        select and highlight given transfer node feature
        '''
        if not self.node_output or not self.node_output.layer:
            return
        self.node_output.layer.removeSelection()
        self.node_output.layer.select(feature.id())
        fid = feature.id()
        for idx in range(len(self.ui.transfer_node_combo)):
            node = self.ui.transfer_node_combo.itemData(idx)
            if node and fid == node.id:
                break
        self.ui.transfer_node_combo.setCurrentIndex(idx)

    def setup_node_params(self, node):
        '''
        set up the parameters of a single transfer node
        '''
        if self.node_params:
            self.node_params.close()
        layout = self.ui.transfer_node_parameter_group.layout()
        clear_layout(layout)
        if not node:
            self.ui.transfer_node_parameter_group.setVisible(False)
            return
        self.ui.transfer_node_parameter_group.setVisible(True)
        #self.ui.transfer_node_parameter_group.setTitle(node.name)
        self.node_params = Params(layout, help_file='verkehr_knoten.txt')
        self.node_params.name = Param(
            node.name, LineEdit(width=300),
            label='Name')

        def save():
            node.name = self.node_params.name.value
            #self.ui.transfer_node_parameter_group.setTitle(node.name)
            node.save()
            self.canvas.refreshAllLayers()
            # lazy way to update the combo box
            self.fill_node_combo(select=node)
            self.setup_weights()

        self.node_params.show(title='Herkunfts-/Zielpunkt bearbeiten')
        self.node_params.changed.connect(save)

        last_row = self.node_params.layout.children()[-1]
        button = QPushButton()
        icon_path = 'iconset_mob/20190619_iconset_mob_delete_1.png'
        icon = QIcon(os.path.join(self.project.settings.IMAGE_PATH, icon_path))
        button.setText('Punkt entfernen')
        button.setIcon(icon)
        button.setToolTip(
            '<p><span style=" font-weight:600;">'
            'Herkunfts-/Zielpunkt entfernen</span>'
            '</p><p>Löscht den aktuell gewählten Herkunfts-/Zielpunkt. '
            '<br/>Dieser Schritt kann nicht rückgängig gemacht werden. </p>')
        last_row.insertWidget(0, button)
        button.clicked.connect(lambda: self.remove_node(node))

    def remove_node(self, node):
        '''
        remove given transfer node
        '''
        if not node:
            return
        reply = QMessageBox.question(
            self.ui.transfer_node_parameter_group,
            'Herkunfts-/Zielpunkt entfernen',
            f'Soll der Punkt "{node.name}" '
            'entfernt werden?',
             QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.itinerary_output:
                self.itinerary_output.remove()
            # workaround: refresg node if weight was changed in the meantime
            node = self.transfer_nodes.get(id=node.id)
            # distribute removed weight
            d = (100 - node.weight) / 100
            node.delete()
            if d > 0:
                for node in self.transfer_nodes:
                    node.weight = round(node.weight / d)
                    node.save()
            # distribute delta caused by rounding errors
            delta = 100 - sum(self.transfer_nodes.values('weight'))
            first = self.transfer_nodes[0]
            first.weight = max(first.weight + delta, 0)
            self.links.table.truncate()
            self.traffic_load.table.truncate()
            self.canvas.refreshAllLayers()
            self.fill_node_combo()
            self.setup_weights()

    def remove_nodes(self):
        '''
        remove all transfer nodes
        '''
        if len(self.transfer_nodes) == 0:
            return
        reply = QMessageBox.question(
            self.ui.transfer_node_parameter_group,
            'Herkunfts-/Zielpunkte entfernen',
            f'Sollen alle Herkunfts-/Zielpunkte entfernt werden?',
             QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.itinerary_output:
                self.itinerary_output.remove()
            self.transfer_nodes.table.truncate()
            self.links.table.truncate()
            self.traffic_load.table.truncate()
            self.canvas.refreshAllLayers()
            self.fill_node_combo()
            self.setup_weights()

    def setup_weights(self):
        '''
        set up the parameters to weight the transfer nodes
        '''
        self.set_status()

        if self.weight_params:
            self.weight_params.close()

        layout = self.ui.weights_group.layout()
        clear_layout(layout)
        self.weight_params = Params(parent=layout,
                                    button_label='Gewichtungen verändern',
                                    help_file='verkehr_gewichtungen.txt')

        dependency = SumDependency(100)
        for node in self.transfer_nodes:
            perc = round(node.weight)
            param = Param(
                perc,
                Slider(maximum=100, lockable=True),
                label=node.name, unit='%'
            )
            self.weight_params.add(param, name=node.name)
            dependency.add(param)

        def save():
            for node in self.transfer_nodes:
                node.weight = self.weight_params[node.name].value
                node.save()
            self.traffic_load.table.truncate()
            self.canvas.refreshAllLayers()
            self.set_status()

        self.weight_params.changed.connect(save)
        self.weight_params.show()

    def setup_ways(self):
        '''
        set up paramaters to set ways
        '''

        if self.ways_params:
            self.ways_params.close()

        if len(self.ways) == 0:
            self.calculate_ways()

        layout = self.ui.ways_group.layout()
        clear_layout(layout)
        self.ways_params = Params(parent=layout,
                                  button_label='Annahmen verändern',
                                  help_file='verkehr_wege.txt')

        for i, way in enumerate(self.ways):
            name = Nutzungsart(way.nutzungsart).name.capitalize()
            self.ways_params.add(Title(name, fontsize=8))
            self.ways_params[f'{name}_gesamt'] = Param(
                way.wege_gesamt, SpinBox(),
                label='Gesamtanzahl der Wege pro Werktag (Hin- und Rückwege)')
            self.ways_params[f'{name}_miv'] = Param(
                way.miv_anteil, SpinBox(maximum=100),
                label='Anteil der von Pkw-Fahrenden gefahrenen Wegen', unit='%')
            if i != len(self.ways) - 1:
                self.ways_params.add(Seperator(margin=0))

        def save():
            for way in self.ways:
                name = Nutzungsart(way.nutzungsart).name.capitalize()
                way.miv_anteil = self.ways_params[f'{name}_miv'].value
                way.wege_gesamt = self.ways_params[f'{name}_gesamt'].value
                way.save()
            self.traffic_load.table.truncate()
            self.canvas.refreshAllLayers()
            self.set_status()

        self.ways_params.changed.connect(save)
        self.ways_params.show()

    def calculate_ways(self):
        '''
        calculate and store the additional ways per type of use of the areas
        '''
        # get ways per type of use
        ways_tou = {}
        self.ways.table.truncate()
        for area in self.areas:
            if area.nutzungsart == 0:
                continue
            entry = ways_tou.get(area.nutzungsart)
            if not entry:
                entry = ways_tou[area.nutzungsart] = [0, 0]
            entry[0] += area.wege_gesamt
            entry[1] += area.wege_miv
        for tou, (wege_gesamt, wege_miv) in ways_tou.items():
            if wege_gesamt == 0:
                continue
            miv_anteil = round(100 * wege_miv / wege_gesamt) # \
                # if wege_gesamt > 0 else 0
            self.ways.add(wege_gesamt=wege_gesamt, nutzungsart=tou,
                          miv_anteil=miv_anteil)

    def set_status(self):
        '''
        sets visibility and active status of certain ui elements depending on
        current state of calculations
        '''
        has_nodes = len(self.transfer_nodes) != 0
        calc_done = len(self.traffic_load) != 0
        self.ui.calculate_traffic_button.setEnabled(has_nodes)
        self.ui.settings_frame.setVisible(has_nodes)
        button_text = 'Straßenverkehrsbelastung anzeigen' if calc_done \
            else 'Straßenverkehrsbelastung berechnen'
        self.ui.calculate_traffic_button.setText(button_text)

    def calculate_nodes(self):
        '''
        calculate the traffic nodes. resets all nodes and results
        '''
        if len(self.transfer_nodes) > 0:
            reply = QMessageBox.question(
                self.ui.transfer_node_parameter_group,
                'Herkunfts-/Zielpunkt entfernen',
                'Die Berechnung der Herkunfts-/Zielpunkte setzt alle '
                'vorhandenen Punkte und Berechnungen zurück.\n'
                'Wollen Sie die Berechnung fortsetzen?',
                 QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        self.transfer_nodes.table.truncate()
        self.links.table.truncate()
        self.traffic_load.table.truncate()
        distance = self.ui.distance_input.value()
        job = TransferNodeCalculation(self.project, distance=distance)
        def on_success(res):
            self.draw_nodes()
            self.draw_itineraries(zoom_to=True)
        def on_close():
            self.fill_node_combo()
            self.setup_weights()
            self.canvas.refreshAllLayers()
        dialog = ProgressDialog(
            job, parent=self.ui, on_success=on_success, on_close=on_close)
        dialog.show()

    def calculate_traffic(self):
        '''
        calculate the traffic load
        '''
        max_dist = getattr(self.settings, 'MAX_AREA_DISTANCE', None)
        points = [c.geom.asPoint() for c in self.connectors]
        xs = [p.x() for p in points]
        ys = [p.y() for p in points]
        if max_dist is not None:
            distances = []
            for i in range(len(points)):
                for j in range(i):
                    dist = np.linalg.norm(
                        np.subtract((xs[i], ys[i]), (xs[j], ys[j])))
                    distances.append(dist)
            if distances and max(distances) > 2 * max_dist:
                QMessageBox.warning(
                    self.ui, 'Hinweis',
                    'Der Abstand zwischen den Anbindungspunkten ist zu groß. '
                    'Er darf für die Schätzung der Verkehrsbelastung jeweils '
                    f'nicht größer als {2 * max_dist} m sein!')
                return

        if len(self.traffic_load) == 0:
            recalculate = len(self.links) == 0
            job = Routing(self.project, recalculate=recalculate)
            def on_success(res):
                if self.itinerary_output:
                    self.itinerary_output.remove()
                self.draw_nodes()
                self.draw_traffic(zoom_to=True)
                self.setup_weights()
            dialog = ProgressDialog(
                job, parent=self.ui,
                on_success=on_success
            )
            dialog.show()
        else:
            self.draw_traffic(zoom_to=True, toggle_if_exists=True)

    def draw_nodes(self, zoom_to=False):
        '''
        show layer visualizing the transfer nodes
        '''
        self.node_output = ProjectLayer.from_table(self.transfer_nodes.table,
                                                   groupname=self.layer_group)
        self.node_output.draw(label='Herkunfts-/Zielpunkte',
                              style_file='verkehr_zielpunkte.qml', prepend=True)
        self.select_tool.set_layer(self.node_output.layer)
        self.drag_tool.set_layer(self.node_output.layer)
        if zoom_to:
            self.node_output.zoom_to()

    def draw_itineraries(self, zoom_to=False):
        '''
        show layer visualizing the itineraries used for determining the
        transfer nodes
        '''
        self.itinerary_output = ProjectLayer.from_table(
            self.itineraries.table, groupname=self.layer_group)
        self.itinerary_output.draw(label='Zulaufstrecken', expanded=False,
                                   style_file='verkehr_kuerzeste_Wege.qml')
        if zoom_to:
            self.itinerary_output.zoom_to()


    def draw_traffic(self, zoom_to=False, toggle_if_exists=False):
        '''
        show layer visualizing the additional traffic load
        '''

        output = ProjectLayer.from_table(self.traffic_load.table,
                                         groupname=self.layer_group)
        output.draw(label='Zusätzliche PKW-Fahrten',
                    style_file='verkehr_links_zusaetzliche_PKW-Fahrten.qml',
                    filter=f'trips > 0', toggle_if_exists=toggle_if_exists,
                    redraw=not toggle_if_exists)
        if zoom_to and output.tree_layer.isVisible():
            output.zoom_to()

    def close(self):
        if self.node_params:
            self.node_params.close()
        if self.ways_params:
            self.ways_params.close()
        if self.weight_params:
            self.weight_params.close()
        self.select_tool.set_active(False)
        self.drag_tool.set_active(False)
        self.add_node_tool.set_active(False)
        super().close()