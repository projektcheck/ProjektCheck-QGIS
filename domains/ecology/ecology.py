# -*- coding: utf-8 -*-
'''
***************************************************************************
    ecology.py
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

domain for the analysis of the ecological impact of the planning areas
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'


from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (QMessageBox, QVBoxLayout,
                                 QTableWidget, QTableWidgetItem,
                                 QAbstractScrollArea, QPushButton)
from qgis.core import QgsWkbTypes
import os

from projektcheck.base.domain import Domain
from projektcheck.base.layers import TileLayer
from projektcheck.base.project import ProjectLayer
from projektcheck.base.tools import PolygonMapTool
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.base.params import (Params, Param, SumDependency)
from projektcheck.base.dialogs import Dialog
from projektcheck.base.inputs import Slider
from projektcheck.utils.utils import clear_layout
from projektcheck.utils.utils import open_file
from .diagrams import Leistungskennwerte, LeistungskennwerteDelta
from .tables import (BodenbedeckungNullfall, BodenbedeckungPlanfall,
                     BodenbedeckungAnteile)

from projektcheck.settings import settings


def remove_junk(geom):
    #if geom.wkbType() != QgsWkbTypes.GeometryCollection:
        #return geom
    mp = None
    for el in geom.asGeometryCollection():
        if el.wkbType() == QgsWkbTypes.LineString or el.area() < 1:
            continue
        if not mp:
            mp = el
        else:
            mp = mp.combine(el)
    return mp


class Ecology(Domain):
    '''
    domain-widget for the analysis of the ecological impact of the planning areas
    '''
    MAX_RATING = 10

    ui_label = 'Ökologie'
    ui_file = 'domain_04-Oeko.ui'
    ui_icon = ('images/iconset_mob/'
               '20190619_iconset_mob_nature_conservation_2.png')
    layer_group = 'Wirkungsbereich 4 - Fläche und Ökologie/Ökologie'

    # ProjektCheck geoserver
    geoserver = settings.GEOSERVER_URL + '/wms?'
    # IÖR wms service
    ioer = 'https://monitor.ioer.de/cgi-bin/wms?'

    # ProjektCheck layers
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

    # IÖR layers
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
        '''
        set up user interactions and drawing tools
        '''
        self.setup_layers()
        self.setup_drawing_tools()
        self.ui.toggle_drawing_button.clicked.connect(self.add_output)
        self.output_nullfall = None
        self.output_planfall = None

        def toggle():
            for tool in self._tools:
                tool.set_active(False)
            self.add_output()
        self.ui.drawing_tab_widget.currentChanged.connect(toggle)

        self.ui.calculate_rating_button.clicked.connect(self.calculate_rating)
        self.ui.import_nullfall_button.clicked.connect(self.import_nullfall)

        for prefix in ['nullfall', 'planfall']:
            button = getattr(self.ui, f'{prefix}_remove_drawing_button')
            button.clicked.connect(
                lambda b, p=prefix: self.clear_drawing(planfall=p=='planfall'))
            button = getattr(self.ui, f'{prefix}_apply_type_button')
            button.clicked.connect(
                lambda b, p=prefix: self.fill_area(
                    self.get_selected_type(p), planfall=p=='planfall'))
            button = getattr(self.ui, f'{prefix}_remove_type_button')
            button.clicked.connect(
                lambda b, p=prefix: self.remove_type(
                    self.get_selected_type(p),
                    planfall=p=='planfall'))
            button = getattr(self.ui, f'{prefix}_analyse_drawing_button')
            button.clicked.connect(
                lambda b, p=prefix: self.show_drawing_analysis(
                    planfall=p=='planfall'))

        self.ui.power_lines_button.clicked.connect(self.add_power_lines)
        self.ui.power_lines_button.setCheckable(False)

        pdf_manual_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Oekologie.pdf')
        self.ui.manual_button.clicked.connect(
            lambda: open_file(pdf_manual_path))

        pdf_rating_path = os.path.join(
            self.settings.HELP_PATH,
            'Erlaeuterung_Kennwerte_Leistungsfaehigkeit_Boden.pdf'
        )
        self.ui.rating_help_button.clicked.connect(
            lambda: open_file(pdf_rating_path))

        def hide_widgets():
            self.ui.toggle_drawing_button.setChecked(False)
            self.ui.drawing_tab_widget.setVisible(False)
        self.ui.rating_groupbox.collapsedStateChanged.connect(
            hide_widgets)
        hide_widgets()

    def add_power_lines(self):
        '''
        add power-lines layer
        '''
        group = (f'{self.project.groupname}/{self.layer_group}')
        layername = '51005_ax_leitung'
        url = (f'url={self.geoserver}&layers={layername}'
               f'&crs=EPSG:{self.settings.EPSG}'
               '&format=image/png&dpiMode=7&styles')
        layer = TileLayer(url, groupname=group)
        layer.draw('Hochspannungsleitungen')

    def load_content(self):
        '''
        load data
        '''
        super().load_content()
        areas = Teilflaechen.features()
        self.area = None
        for area in areas:
            if not self.area:
                self.area = area.geom
            else:
                self.area = self.area.combine(area.geom)
        self.boden_nullfall = BodenbedeckungNullfall.features(create=True)
        self.boden_planfall = BodenbedeckungPlanfall.features(create=True)
        self.anteile = BodenbedeckungAnteile.features(create=True)
        self.bb_types = self.basedata.get_table(
            'Bodenbedeckung', 'Flaeche_und_Oekologie'
        )
        self.faktoren = self.basedata.get_table(
            'Faktoren', 'Flaeche_und_Oekologie'
        )

        self.output_nullfall = ProjectLayer.from_table(
            self.boden_nullfall.table, groupname=self.layer_group,
            prepend=True)
        self.output_planfall = ProjectLayer.from_table(
            self.boden_planfall.table, groupname=self.layer_group,
            prepend=True)
        self.setup_params()

    def setup_params(self):
        '''
        set up the parameter for setting the percentages of ground cover in
        status quo and the scenario
        '''
        self.params_nullfall = Params(
            self.ui.param_nullfall_tab.layout(),
            help_file='oekologie_bodenbedeckung_nullfall.txt')
        self.params_planfall = Params(
            self.ui.param_planfall_tab.layout(),
            help_file='oekologie_bodenbedeckung_planfall.txt')
        clear_layout(self.ui.param_nullfall_tab.layout())
        clear_layout(self.ui.param_planfall_tab.layout())

        def apply_nf():
            self.apply_drawing(False)
        def apply_pf():
            self.apply_drawing(True)

        for params, prefix in [(self.params_nullfall, 'nullfall'),
                               (self.params_planfall, 'planfall')]:
            planfall = prefix == 'planfall'
            dependency = SumDependency(100)
            for bb_typ in self.bb_types.features():
                bb_id = bb_typ.IDBodenbedeckung
                feature = self.anteile.get(IDBodenbedeckung=bb_id,
                                           planfall=planfall)
                value = feature.anteil if feature else 0
                slider = Slider(maximum=100, width=200, lockable=True)
                param = Param(
                    int(value), slider, label=bb_typ.name,
                    unit='%'
                )
                dependency.add(param)
                params.add(param, name=f'{prefix}_{bb_id}')
            params.changed.connect(lambda p=prefix: self.save(p))
            params.show(title='Flächenanteile der Bodenbedeckung für die '
                        f'Analyse: {prefix.capitalize()}')
            last_row = params.layout.children()[-1]
            button = QPushButton()
            button.setText('aus Zeichnung übernehmen')
            last_row.insertWidget(0, button)
            # workaround: lambda with argument didn't seem to work here (weird)
            #button.clicked.connect(lambda p=planfall: self.apply_drawing(p))
            func = apply_pf if planfall else apply_nf
            button.clicked.connect(func)

    def setup_layers(self):
        '''
        add ProjektCheck geoserver and IÖR layers
        '''
        def add_layer_from_dict(layers, parent_group):
            for name, url in layers:
                self.add_wms_layer(name, url, parent_group=parent_group)

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

    def setup_drawing_tools(self):
        '''
        set up the tools for drawing the ground cover in status quo and
        the scenario
        '''
        self._tools = []
        self.drawing_tools = {
            'draw_builtup_button': 1,
            'draw_water_button': 2,
            'draw_plates_button': 3,
            'draw_trees_button': 4,
            'draw_perennial_button': 5,
            'draw_meadow_button': 6,
            'draw_lawn_button': 7,
            'draw_cover_button': 8,
            'draw_concrete_button': 9,
            'draw_field_button': 10,
            'draw_paving_button': 11
        }

        for prefix in ['nullfall', 'planfall']:
            is_planfall = prefix == 'planfall'
            for button_name, floor_id in self.drawing_tools.items():
                button = getattr(self.ui, f'{prefix}_{button_name}')
                check = getattr(self.ui, f'{prefix}_in_area_only_check')
                tool = PolygonMapTool(button, canvas=self.canvas,
                                      draw_markers=True,
                                      line_style=Qt.DotLine)
                tool.drawn.connect(
                    lambda geom, i=floor_id, p=is_planfall, c=check:
                    self.add_geom(
                        geom, i, in_area_only=c.isChecked(), planfall=p
                    )
                )
                self._tools.append(tool)

    def add_geom(self, geom, typ, unite=True, in_area_only=True,
                 difference=True, planfall=True):
        '''
        add a geometry to the database belonging to a specific ground cover type
        '''
        if typ is None or not geom.isGeosValid():
            return
        if in_area_only:
            geom = geom.intersection(self.area)
        if not geom.isGeosValid():
            geom = geom.makeValid()
        if geom.isEmpty() or geom.isNull():
            return
        features = self.boden_planfall if planfall else self.boden_nullfall
        if not unite:
            features.add(geom=geom, IDBodenbedeckung=typ, area=geom.area())
        # merge with existing geometries of same type
        else:
            ex_feat = features.get(IDBodenbedeckung=typ)
            if not ex_feat:
                features.add(geom=geom, IDBodenbedeckung=typ,
                             area=geom.area())
            else:
                merged = ex_feat.geom.combine(geom)
                if not merged.isGeosValid():
                    merged = merged.makeValid()
                merged = remove_junk(merged)
                # ignore geometry if it can not be merged
                if not merged or merged.isEmpty() or merged.isNull():
                    return
                ex_feat.geom = merged
                ex_feat.area = ex_feat.geom.area()
                ex_feat.save()
        # cut existing geometries of a different type at same place
        if difference:
            marked_for_deletion = []
            for feature in features:
                if feature.IDBodenbedeckung == typ:
                    continue
                difference = feature.geom.difference(geom)
                if not difference.isGeosValid():
                    difference = difference.makeValid()
                difference = remove_junk(difference)
                if (not difference or difference.isNull() or
                    difference.isEmpty()):
                    marked_for_deletion.append(feature)
                    continue
                feature.geom = difference
                feature.area = difference.area()
                feature.save()
            for feature in marked_for_deletion:
                feature.delete()
        self.canvas.refreshAllLayers()

        if len(features) == 1:
            self.add_output(redraw=True)

    def fill_area(self, typ, planfall=True):
        #self.clear_drawing(planfall=planfall)
        self.add_geom(self.area, typ, planfall=planfall)

    def remove_type(self, typ, planfall=True):
        '''
        remove all geometries of a specific ground cover type from database
        '''
        if not typ:
            return
        features = self.boden_planfall if planfall else self.boden_nullfall
        # ToDo: filter would be better but messes up original filter atm
        for feature in features:
            if feature.IDBodenbedeckung == typ:
                feature.delete()
        self.canvas.refreshAllLayers()

    def save(self, prefix):
        '''
        save ground cover shares set by user for status quo ('nullfall') or
        the scenario ('planfall')
        '''
        planfall = prefix == 'planfall'
        params = self.params_planfall if planfall else self.params_nullfall
        for bb_typ in self.bb_types.features():
            bb_id = bb_typ.IDBodenbedeckung
            feature = self.anteile.get(IDBodenbedeckung=bb_id,
                                       planfall=planfall)

            if not feature:
                feature = self.anteile.add(IDBodenbedeckung=bb_id)
                feature.planfall = planfall
            feature.anteil = params.get(f'{prefix}_{bb_id}').value
            feature.save()

    def import_nullfall(self):
        '''
        import drawing of status quo into the scenario
        '''
        if len(self.boden_planfall) > 0:
            reply = QMessageBox.question(
                self.ui, 'Nullfall in Planfall importieren',
                'Achtung: die existierende Zeichnung für den Planfall '
                'wird beim Import des Nullfalls gelöscht.',
                QMessageBox.Yes, QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
        self.boden_planfall.delete()
        for feature in self.boden_nullfall:
            self.boden_planfall.add(geom=feature.geom,
                                    IDBodenbedeckung=feature.IDBodenbedeckung,
                                    area=feature.geom.area())
        self.add_output()

    def get_selected_type(self, prefix):
        '''
        currently selected ground cover type
        '''
        for button_name, typ in self.drawing_tools.items():
            button = getattr(self.ui, f'{prefix}_{button_name}')
            if button.isChecked():
                return typ
        return None

    def analyse_shares(self, planfall=True):
        '''
        calculate the share per ground cover type out of the drawing
        '''
        features = self.boden_planfall if planfall else self.boden_nullfall
        df = features.to_pandas()
        grouped = df.groupby('IDBodenbedeckung')
        grouped_sums = grouped['area'].sum()
        sum_area = df['area'].sum()
        shares = (grouped_sums * 100 / sum_area).round() if sum_area > 0 \
            else grouped_sums
        return shares

    def apply_drawing(self, planfall=True):
        '''
        calculate ground cover shares and write them to database
        '''
        shares = self.analyse_shares(planfall)
        params = self.params_planfall if planfall else self.params_nullfall
        prefix = 'planfall' if planfall else 'nullfall'
        for bb_typ in self.bb_types.features():
            bb_id = bb_typ.IDBodenbedeckung
            params.get(f'{prefix}_{bb_id}').value = int(shares.get(bb_id) or 0)
        self.save(prefix)

    def show_drawing_analysis(self, planfall=True):
        '''
        open shares of ground cover in dialog with table
        '''
        shares = self.analyse_shares(planfall)
        l = 'Planfall' if planfall else 'Nullfall'
        dialog = Dialog(
            title='Flächenanteile der Bodenbedeckung in '
            f'der Zeichnung für den {l}'
        )
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        table_widget = QTableWidget()
        layout.addWidget(table_widget)
        table_widget.setColumnCount(2)
        table_widget.setHorizontalHeaderItem(
            0, QTableWidgetItem('Bodenbedeckungstyp'))
        table_widget.setHorizontalHeaderItem(
            1, QTableWidgetItem('Anteil'))
        types = self.bb_types.features()
        table_widget.setRowCount(len(types))
        for i, bb_typ in enumerate(types):
            share = shares.get(bb_typ.IDBodenbedeckung) or 0
            table_widget.setItem(i, 0, QTableWidgetItem(bb_typ.name))
            table_widget.setItem(i, 1, QTableWidgetItem(f'{share}%'))
        table_widget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        table_widget.resizeColumnsToContents()
        dialog.showEvent = lambda e: dialog.adjustSize()
        dialog.show()

    def clear_drawing(self, planfall=True):
        '''
        remove all drawn elements
        '''
        l = 'Planfall' if planfall else 'Nullfall'
        reply = QMessageBox.question(
            self.ui, 'Zeichnung löschen',
            f'Sollen alle gezeichneten Flächen für den {l} entfernt werden?',
            QMessageBox.Yes, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        features = self.boden_planfall if planfall else self.boden_nullfall
        output = self.output_planfall if planfall \
            else self.output_nullfall
        layer = output.layer
        # remove selection, so that qgis is free to remove them from canvas
        layer.removeSelection()
        features.delete()
        self.canvas.refreshAllLayers()

    def add_output(self, redraw=False):
        '''
        add drawings as layer
        '''
        planfall = self.ui.drawing_tab_widget.currentIndex() == 1
        label = 'Bodenbedeckung '
        label += 'Planfall' if planfall else 'Nullfall'
        output = self.output_planfall if planfall else self.output_nullfall
        style = 'flaeche_oekologie_bodenbedeckung_planfall.qml' if planfall \
            else 'flaeche_oekologie_bodenbedeckung_nullfall.qml'
        output.draw(label=label, style_file=style, redraw=redraw)
        setattr(self, 'output_planfall' if planfall else 'output_nullfall',
                output)
        disabled_out = self.output_nullfall if planfall \
            else self.output_planfall
        if disabled_out:
            disabled_out.set_visibility(False)

    def add_wms_layer(self, name, url, parent_group=None):
        '''
        add a wms layer
        '''
        group = (f'{self.project.groupname}/{self.layer_group}')
        if parent_group:
            group += f'/{parent_group}'
        url = (f'{url}&crs=EPSG:{self.settings.EPSG}'
               '&format=image/png&dpiMode=7&styles')
        layer = TileLayer(url, groupname=group)
        layer.draw(name, toggle_if_exists=True)

    def calculate_rating(self):
        '''
        calculate the ratings based on the ground covers for status quo and
        the scenario. Plot the results in diagrams
        '''
        df_factors = self.faktoren.to_pandas()
        df_shares = self.anteile.to_pandas()
        df_merged = df_shares.merge(df_factors, on='IDBodenbedeckung')

        def rating(df, columns):
            df_rating = df.multiply(df['anteil']/100, axis='index')
            df_rating = df_rating[columns]
            df_rating = df_rating.sum(axis=0)

            rating = df_rating * self.MAX_RATING

            ## divide the domain (0..1) into n + 1 bins
            ## -> n is the max. rating value
            #bins = np.linspace(0, 1, self.MAX_RATING+1)
            #rating = np.digitize(df_rating, bins) - 1
            return rating.round(1)

        columns = df_factors.columns[3:]
        df_merged_nf = df_merged[df_merged['planfall']==False]
        df_merged_pf = df_merged[df_merged['planfall']==True]
        rating_nf = rating(df_merged_nf, columns)
        rating_pf = rating(df_merged_pf, columns)
        rating_delta = rating_pf - rating_nf
        categories = [c.split('_')[0].capitalize() for c in columns]
        columns = [c.split('_')[1] for c in columns]
        columns = [c.replace('ae', 'ä').replace('ue', 'ü').replace('oe', 'ö')
                   .capitalize() for c in columns]

        diagram = Leistungskennwerte(
            nullfall=rating_nf, planfall=rating_pf,
            columns=columns,
            categories=categories,
            title='Leistungskennwerte im Nullfall und Planfall',
            max_rating=self.MAX_RATING
        )
        diagram.draw()

        diagram = LeistungskennwerteDelta(
            delta=rating_delta, columns=columns,
            categories=categories,
            title='Beeinträchtigung durch Planungsvorhaben (= Veränderung der '
            '\nLeistungskennwerte im Planfall gegenüber dem Nullfall)',
            max_rating=self.MAX_RATING)
        diagram.draw(offset_x=100, offset_y=100)

    def close(self):
        '''
        close parameters and drawing tools
        '''
        if hasattr(self, 'params_nullfall'):
            self.params_nullfall.close()
        if hasattr(self, 'params_planfall'):
            self.params_planfall.close()
        for tool in self._tools:
            tool.set_active(False)
        super().close()
