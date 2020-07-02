# -*- coding: utf-8 -*-
'''
***************************************************************************
    tables.py
    ---------------------
    Date                 : September 2019
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

project database tables of the domain market-competition holding markets and
their relations
'''

__author__ = 'Christoph Franke'
__date__ = '13/09/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class Centers(ProjectTable):

    name = Field(str, '')
    nutzerdefiniert = Field(int, -1)
    umsatz_differenz = Field(int, 0)
    umsatz_planfall = Field(int, 0)
    umsatz_nullfall = Field(int, 0)
    auswahl = Field(int, 0)
    ags = Field(str, '')
    rs = Field(str, '')
    ew = Field(int, 0)
    kk = Field(float, 0)
    zentralitaet_nullfall = Field(float, 0)
    zentralitaet_planfall = Field(float, 0)
    zentralitaet_differenz = Field(float, 0)
    vkfl_dichte_nullfall = Field(float, 0)
    vkfl_dichte_planfall = Field(float, 0)
    vkfl_dichte_differenz = Field(float, 0)

    class Meta:
        workspace = 'marketcompetition'


class Markets(ProjectTable):

    name = Field(str, '')
    AGS = Field(str, '')
    adresse = Field(str, '')
    id_teilflaeche = Field(int, -1)
    id_betriebstyp_nullfall = Field(int, 0)
    betriebstyp_nullfall = Field(str, '')
    id_betriebstyp_planfall = Field(int, 0)
    betriebstyp_planfall = Field(str, '')
    id_kette = Field(int, 0)
    kette = Field(str, '')
    umsatz_nullfall = Field(float, 0)
    umsatz_planfall = Field(float, 0)
    umsatz_differenz = Field(float, 0)
    is_buffer = Field(bool, False)
    is_osm = Field(bool, False)
    vkfl = Field(int, 0)
    vkfl_planfall = Field(int, 0)

    class Meta:
        workspace = 'marketcompetition'


class MarketCellRelations(ProjectTable):

    id_markt = Field(int, 0)
    id_siedlungszelle = Field(int, 0)
    distanz = Field(int, 0)
    kk_strom_nullfall = Field(float, 0)
    kk_strom_planfall = Field(float, 0)
    kk_bindung_nullfall = Field(float, 0)
    kk_bindung_planfall = Field(float, 0)
    in_auswahl = Field(bool, False)
    luftlinie = Field(int, 0)

    class Meta:
        workspace = 'marketcompetition'


class SettlementCells(ProjectTable):
    ew = Field(int, 0)
    kk_index = Field(float, 1)
    kk = Field(float, 0)
    id_teilflaeche = Field(int, 0)
    in_auswahl = Field(bool, False)
    ags = Field(str, '')

    class Meta:
        workspace = 'marketcompetition'


class Settings(ProjectTable):
    sz_puffer = Field(int, 0)
    betrachtungsraum = Field(str, '')

    class Meta:
        workspace = 'marketcompetition'




