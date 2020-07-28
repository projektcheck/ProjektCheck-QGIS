# -*- coding: utf-8 -*-
'''
***************************************************************************
    tables.py
    ---------------------
    Date                 : May 2020
    Copyright            : (C) 2020 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

project database tables of the municipal tax revenue domain
'''

__author__ = 'Christoph Franke'
__date__ = '18/05/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class Gemeindebilanzen(ProjectTable):
    RS = Field(str, '')
    AGS = Field(str, '')
    GEN = Field(str, '')
    BEZ = Field(str, '')
    IBZ = Field(float, 0)
    BEM = Field(str, )
    Einwohner = Field(int, 0)
    SvB = Field(int, 0)
    SvB_pro_Ew = Field(float, 0)
    Hebesatz_GewSt = Field(int, 0)
    grundsteuer = Field(int, 0)
    einkommensteuer = Field(int, 0)
    gewerbesteuer = Field(int, 0)
    umsatzsteuer = Field(int, 0)
    fam_leistungs_ausgleich = Field(int, 0)
    summe_einnahmen = Field(int, 0)

    class Meta:
        workspace = 'einnahmen'


class EinwohnerWanderung(ProjectTable):
    AGS = Field(str, '')
    GEN = Field(str, '')
    zuzug = Field(float, 0)
    fortzug = Field(float, 0)
    saldo = Field(float, 0)
    fixed = Field(bool, False)
    wanderungs_anteil = Field(float, 0)

    class Meta:
        workspace = 'einnahmen'


class BeschaeftigtenWanderung(ProjectTable):
    AGS = Field(str, '')
    GEN = Field(str, '')
    zuzug = Field(float, 0)
    fortzug = Field(float, 0)
    saldo = Field(float, 0)
    fixed = Field(bool, False)
    wanderungs_anteil = Field(float, 0)

    class Meta:
        workspace = 'einnahmen'


class GrundsteuerSettings(ProjectTable):
    Hebesatz_GrStB = Field(int, 0)
    EFH_Rohmiete = Field(int, 0)
    DHH_Rohmiete = Field(int, 0)
    RHW_Rohmiete = Field(int, 0)
    MFH_Rohmiete = Field(int, 0)
    Bodenwert_SWV = Field(int, 0)
    Bueroflaeche = Field(int, 0)
    Verkaufsraeume = Field(int, 0)
    qm_Grundstueck_pro_WE_EFH = Field(int, 0)
    is_new_bundesland = Field(bool, True)

    class Meta:
        workspace = 'einnahmen'




