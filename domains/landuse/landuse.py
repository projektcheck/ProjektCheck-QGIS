# -*- coding: utf-8 -*-
'''
***************************************************************************
    jobs_inhabitants.py
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

domain for the analysis of landuse
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

import os

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.base.diagrams import BarChart, PieChart
from projektcheck.domains.definitions.tables import (Wohneinheiten,
                                                     Projektrahmendaten)
from projektcheck.domains.constants import Nutzungsart
from projektcheck.base.params import Params, Param, Title, Seperator
from projektcheck.base.inputs import Slider
from projektcheck.utils.utils import clear_layout
from projektcheck.base.tools import LineMapTool
from projektcheck.utils.utils import open_file
from .tables import (WohnbaulandAnteile, WohnflaecheGebaeudetyp,
                     GrenzeSiedlungskoerper)


class LandUse(Domain):
    '''
    domain-widget calculating and visualizing the residential density and the
    integrated position of the planning area
    '''

    ui_label = 'Flächeninanspruchnahme'
    ui_file = 'domain_05-Fl.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_landuse_1.png"
    layer_group = ('Wirkungsbereich 4 - Fläche und Ökologie/'
                   'Flächeninanspruchnahme')

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(
            lambda: self.change_area())
        self.layout = self.ui.parameter_group.layout()
        self.ui.calculate_density_button.clicked.connect(
            self.calculate_wohndichte)
        self.ui.calculate_areadensity_button.clicked.connect(
            self.calculate_wohnflaechendichte)
        self.ui.calculate_integration_button.clicked.connect(
            self.calculate_integration)
        self.bordertool = LineMapTool(
            self.ui.draw_border_button, canvas=self.canvas,
            line_width=3)# , color='#33ccff')
        self.bordertool.drawn.connect(self.add_border)

        self.ui.remove_drawing_button.clicked.connect(self.remove_borders)

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Flaecheninanspruchnahme.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

    def load_content(self):
        super().load_content()
        self.gebaeudetypen_base = self.basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        )
        self.areas = Teilflaechen.features()
        self.residential_areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.WOHNEN.value)
        self.wohnbauland_anteile = WohnbaulandAnteile.features(create=True)
        self.wohnflaeche = WohnflaecheGebaeudetyp.features(create=True)
        self.borders = GrenzeSiedlungskoerper.features(create=True)
        self.wohneinheiten = Wohneinheiten.features(create=True)
        self.rahmendaten = Projektrahmendaten.features()[0]
        self.wohndichte_kreis = self.basedata.get_table(
            'Wohndichte_Wohnflaechendichte_Kreise', 'Flaeche_und_Oekologie')
        self.wohndichte_raumtyp = self.basedata.get_table(
            'Wohndichte_Wohnflaechendichte_RaumTypen',
            'Flaeche_und_Oekologie')
        self.raumtypen = self.basedata.get_table(
            'RaumTypen', 'Flaeche_und_Oekologie')

        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        for area in self.residential_areas:
            self.ui.area_combo.addItem(area.name, area)
        self.ui.area_combo.blockSignals(False)

        self.add_border_output()

        self.change_area()

        self.area_union = None
        # ToDo: fix filter side effects
        self.areas.filter()
        for area in self.areas:
            self.area_union = area.geom if not self.area_union \
                else self.area_union.combine(area.geom)
        # buffer to fill gaps
        self.area_union = self.area_union.buffer(0.1, 6)
        self.bordertool.set_snap_geometry(self.area_union)

    def setup_params(self):
        '''
        set up the parameters for editing the mean residential area per
        appartment and the net share of residential building land in the active
        area
        '''

        anteil = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        value = anteil.nettoflaeche if anteil else 85
        clear_layout(self.layout)

        self.params = Params(
            self.layout,
            help_file='flaecheninanspruchnahme_wohnbauland_wohnflaeche.txt'
        )

        self.params.add(Title('Anteil Nettowohnbauland'))
        self.params.nettoflaeche = Param(
            int(value), Slider(maximum=100),
            label='Anteil des Nettowohnbaulandes (= Summe aller\n'
            'Wohnbaugrundstücke) an der Gesamtfläche der\n'
            'ausgewählten Teilfläche',
            unit='%'
        )

        self.params.add(Seperator())

        self.params.add(Title('Durchschnittliche Wohnfläche je Wohnung'))

        for bt in self.gebaeudetypen_base.features():
            param_name = bt.param_we
            feature = self.wohnflaeche.get(id_gebaeudetyp=bt.id,
                                           id_teilflaeche=self.area.id)
            # default value on first time
            value = bt.Wohnfl_m2_pro_WE if not feature \
                else feature.mean_wohnflaeche
            self.params.add(Param(
                value, Slider(maximum=200),
                label=f'... in {bt.display_name}', unit='m²'),
                name=param_name
            )

        self.params.changed.connect(self.save)
        self.params.show(
            title='Annahmen für Wohnungsdichte und Wohnflächendichte')

        self.save()

    def save(self):
        '''
        save the current settings of the parameters
        '''
        feature = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        # ToDo: get_or_create
        if not feature:
            feature = self.wohnbauland_anteile.add(id_teilflaeche=self.area.id)
        feature.nettoflaeche = self.params.nettoflaeche.value
        feature.save()

        for bt in self.gebaeudetypen_base.features():
            feature = self.wohnflaeche.get(id_gebaeudetyp=bt.id,
                                           id_teilflaeche=self.area.id)
            if not feature:
                feature = self.wohnflaeche.add(
                    id_gebaeudetyp=bt.id, id_teilflaeche=self.area.id)
            feature.mean_wohnflaeche = getattr(
                self.params, bt.param_we).value
            feature.save()

    def change_area(self):
        '''
        set currently selected area as active area
        '''
        self.area = self.ui.area_combo.itemData(
            self.ui.area_combo.currentIndex())
        if not self.area:
            return

        output = ProjectLayer.find('Umriss des Plangebiets')
        if output:
            layer = output[0].layer()
            layer.removeSelection()
            layer.select(self.area.id)

        self.setup_params()

    def calculate_wohndichte(self):
        '''
        calculate residential density and show chart of results
        '''
        if not self.area:
            return
        # calculation for area
        anteil = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        netto_wb = (self.area.geom.area() / 10000) * (anteil.nettoflaeche / 100)
        wohndichte = round(self.area.we_gesamt / netto_wb, 1) \
            if netto_wb > 0 else 0

        # get data to compare to
        kreis, kreisname, kreistyp, typname = self.get_kreis_data()
        wohndichte_kreis = kreis.Wohndichte_WE_pro_ha_Nettowohnbauland
        wohndichte_kreistyp = kreistyp.Wohndichte_WE_pro_ha_Nettowohnbauland

        # chart
        values = [wohndichte, wohndichte_kreis, wohndichte_kreistyp]
        labels = [f'Teilfläche "{self.area.name}"', f'Kreis "{kreisname}"',
                  typname]
        colors = ['#70ad47', '#385723', '#385723']
        custom_legend={
            f'Teilfläche "{self.area.name}"': '#70ad47',
            'Vergleichswerte': '#385723'
        }
        chart = BarChart(
            values, labels=labels,
            title=f'Teilfläche "{self.area.name}": '
            'Wohneinheiten pro Hektar Nettowohnbauland',
            y_label='Wohneinheiten pro Hektar Nettowohnbauland',
            colors=colors, custom_legend=custom_legend
        )
        chart.draw()

    def calculate_wohnflaechendichte(self):
        '''
        calculate density of living areas and show results as chart
        '''
        if not self.area:
            return
        # calculation for area
        anteil = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        wohneinheiten = self.wohneinheiten.filter(id_teilflaeche=self.area.id)
        wohnflaeche = self.wohnflaeche.filter(id_teilflaeche=self.area.id)

        df_wohneinheiten = wohneinheiten.to_pandas()
        df_wohnflaeche = wohnflaeche.to_pandas()
        df_merged = df_wohneinheiten.merge(df_wohnflaeche, on='id_gebaeudetyp')
        wohnflaeche_gesamt = (df_merged['mean_wohnflaeche'] *
                              df_merged['we']).sum()
        netto_wb = (self.area.geom.area() / 10000) * (anteil.nettoflaeche / 100)
        wohnflaechendichte = round(wohnflaeche_gesamt / netto_wb)\
            if netto_wb > 0 else 0

        # get data to compare to
        kreis, kreisname, kreistyp, typname = self.get_kreis_data()
        wohndichte_kreis = \
            round(kreis.Wohnflaechendichte_qm_Wohnfl_pro_ha_Nettowohnbauland)
        wohndichte_kreistyp = \
            round(kreistyp.Wohnflaechendichte_qm_Wohnfl_pro_ha_Nettowohnbauland)

        # chart
        values = [wohnflaechendichte, wohndichte_kreis, wohndichte_kreistyp]
        values = [round(v) for v in values]
        labels = [f'Teilfläche "{self.area.name}"',
                  f'Kreis {kreisname}', typname]
        colors = ['#70ad47', '#385723', '#385723']
        custom_legend={
            f'Teilfläche "{self.area.name}"': '#70ad47',
            'Vergleichswerte': '#385723'
        }
        chart = BarChart(
            values, labels=labels,
            title=f'Teilfläche "{self.area.name}": '
            'Wohnfläche (m²) pro Hektar Nettowohnbauland',
            colors=colors, custom_legend=custom_legend,
            y_label='Quadratmeter Wohnfläche pro Hektar Nettowohnbauland'
        )
        chart.draw()

    def get_kreis_data(self) -> tuple:
        '''
        get comparable data of muncipality of planning area
        '''
        ags5 = str(self.rahmendaten.ags)[0:5]
        kreis = self.wohndichte_kreis.features().get(AGS5=ags5)
        kreistyp_id = kreis.Siedlungsstruktureller_Kreistyp
        kreistyp = self.wohndichte_raumtyp.features().get(
            Siedlungsstruktureller_Kreistyp=kreistyp_id)
        kreisname = kreis.Kreis_kreisfreie_Stadt.split(',')[0]
        typname = self.raumtypen.features().get(ID=kreistyp_id).Name
        return kreis, kreisname, kreistyp, typname

    def add_border(self, geom):
        '''
        add a geometry to the drawn border
        '''
        self.borders.add(geom=geom)
        # workaround: layer style is not applied correctly
        # with empty features -> redraw on first geometry
        if len(self.borders) == 1:
            self.add_border_output()
        self.canvas.refreshAllLayers()

    def remove_borders(self):
        '''
        remove drawn border
        '''
        self.borders.delete()
        self.canvas.refreshAllLayers()

    def add_border_output(self):
        '''
        add layer to visualize drawn border
        '''
        self.output_border = ProjectLayer.from_table(
            self.borders.table, groupname=self.layer_group,
            prepend=True)
        self.output_border.draw(
            label='Grenze Siedlunskörper',
            style_file='flaeche_oekologie_grenze_siedlungskoerper.qml'
        )

    def calculate_integration(self):
        '''
        calculate integration shares from drawing and show results in a
        pie chart
        '''
        area_outer_border = self.area_union.length()
        drawn_borders = sum([line.geom.length() for line in self.borders])
        shared_border = round(100 * drawn_borders / area_outer_border)
        shared_border = min(shared_border, 100)
        values = [shared_border, 100 - shared_border]
        labels = ['Anteil der Plangebietsgrenze,\n'
                  'die an bestehende Siedlungs-\n'
                  'flächen angrenzt',
                  'Anteil der Plangebietsgrenze,\n'
                  'die nicht an bestehende\n'
                  'Siedlungsflächen angrenzt',]
        chart = PieChart(values, labels=labels,
                         title=f'{self.project.name}: Lage zu bestehenden '
                         'Siedlungsflächen', decimals=0)
        chart.draw()

    def close(self):
        '''
        close parameters and drawing tools
        '''
        # ToDo: implement this in project (collecting all used workscpaces)
        output = ProjectLayer.find('Umriss des Plangebiets')
        if output:
            layer = output[0].layer()
            layer.removeSelection()
        if hasattr(self, 'params'):
            self.params.close()
        self.bordertool.set_active(False)
        super().close()