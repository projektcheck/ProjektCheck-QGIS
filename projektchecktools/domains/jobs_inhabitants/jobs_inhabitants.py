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

domain for the analysis of job and population development
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

import os
from qgis.PyQt.QtWidgets import QMessageBox
from qgis import utils

from projektchecktools.base.domain import Domain
from projektchecktools.domains.constants import Nutzungsart
from projektchecktools.domains.jobs_inhabitants.diagrams import (
    BewohnerEntwicklung, ArbeitsplatzEntwicklung, BranchenAnteile)
from projektchecktools.domains.definitions.tables import Teilflaechen
from projektchecktools.utils.utils import open_file
from projektchecktools.base.project import ProjectLayer
from projektchecktools.domains.definitions.tables import Gewerbeanteile
from projektchecktools.domains.jobs_inhabitants.tables import (
    WohnenProJahr, ApProJahr)


class JobsInhabitants(Domain):
    '''
    domain-widget visualizing the development of jobs and inhabitants
    '''
    ui_label = 'Bewohner und Arbeitsplätze'
    ui_file = 'domain_01-BA.ui'
    ui_icon = 'images/iconset_mob/20190619_iconset_mob_people_1.png'
    layer_group = 'Wirkungsbereich 1 - Bewohner und Arbeitsplätze'

    def setupUi(self):
        self.ui.inhabitants_button.clicked.connect(self.inhabitants_diagram)
        self.ui.jobs_button.clicked.connect(self.jobs_diagram)
        self.ui.inhabitants_table_button.clicked.connect(self.inhabitants_table)
        self.ui.jobs_table_button.clicked.connect(self.jobs_table)

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Bewohner_und_Arbeitsplätze.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

    def load_content(self):
        super().load_content()
        output = ProjectLayer.find('Projektdefinition')
        if output:
            output[0].setItemVisibilityChecked(True)

    def get_residential_areas(self):
        '''
        validate and return residential areas
        '''
        areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.WOHNEN.value,
            we_gesamt__gt=0
        )
        if len(areas) == 0:
            QMessageBox.warning(
                self.ui, 'Bewohner',
                'Es wurden keine Teilflächen mit definierter '
                'Wohnnutzung gefunden'
            )
            return []
        return areas

    def get_job_areas(self):
        '''
        validate and return commercial areas
        '''
        areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.GEWERBE.value,
            ap_gesamt__gt=0
        )
        if len(areas) == 0:
            QMessageBox.warning(
                self.ui, 'Arbeitsplätze',
                'Es wurden keine Teilflächen mit definierter '
                'Gewerbenutzung gefunden'
            )
            return []
        return areas

    def inhabitants_diagram(self):
        '''
        show chart of population development
        '''
        areas = self.get_residential_areas()
        if not areas:
            return
        for i, area in enumerate(areas):
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Einwohnerentwicklung")
            diagram = BewohnerEntwicklung(area=area, title=title)
            diagram.draw(offset_x=i*100, offset_y=i*100)

    def jobs_diagram(self):
        '''
        show chart of job development
        '''
        areas = self.get_job_areas()
        if not areas:
            return
        for i, area in enumerate(areas):
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Anzahl Arbeitsplätze (Orientierungswerte)")
            diagram = ArbeitsplatzEntwicklung(area=area, title=title)
            diagram.draw(offset_x=i*100, offset_y=i*100)

            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Branchenanteile an den Arbeitsplätzen")
            diagram = BranchenAnteile(area=area, title=title)
            diagram.draw(offset_x=i*100+50, offset_y=i*100+50)

    def inhabitants_table(self):
        '''
        show population development in a table a dialog
        '''
        areas = self.get_residential_areas()
        if not areas:
            return
        output = ProjectLayer.from_table(
            WohnenProJahr.get_table(), groupname=self.layer_group)
        layer = output.draw(label='Bewohnerschätzung nach Alter und Jahr')
        table_config = layer.attributeTableConfig()
        table_config.setSortExpression(
            '"id_teilflaeche" || "jahr" || "id_altersklasse"')
        layer.setAttributeTableConfig(table_config)
        utils.iface.showAttributeTable(layer)

    def jobs_table(self):
        '''
        show job development in a table a dialog
        '''
        areas = self.get_job_areas()
        if not areas:
            return
        output = ProjectLayer.from_table(
            ApProJahr.get_table(), groupname=self.layer_group)
        layer = output.draw(label='Arbeitsplätze insgesamt nach Jahr')
        table_config = layer.attributeTableConfig()
        table_config.setSortExpression('"id_teilflaeche" || "jahr"')
        layer.setAttributeTableConfig(table_config)
        utils.iface.showAttributeTable(layer)

        output = ProjectLayer.from_table(
            Gewerbeanteile.get_table(), groupname=self.layer_group)
        layer = output.draw(label='Branchenanteile')
        table_config = layer.attributeTableConfig()
        table_config.setSortExpression('"id_teilflaeche" || "id_branche"')
        layer.setAttributeTableConfig(table_config)
        utils.iface.showAttributeTable(layer)
