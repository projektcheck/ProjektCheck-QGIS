# -*- coding: utf-8 -*-
'''
***************************************************************************
    tables.py
    ---------------------
    Date                 : February 2020
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

project database tables of infrastructural costs domain
'''

__author__ = 'Christoph Franke'
__date__ = '03/02/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class ErschliessungsnetzLinienZeichnung(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    length = Field(float, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class ErschliessungsnetzLinien(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    Netzelement = Field(str, '')
    length = Field(float, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class ErschliessungsnetzPunkte(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    bezeichnung = Field(str, '')
    Euro_EH = Field(float, 0)
    Euro_EN = Field(float, 0)
    Cent_BU = Field(int, 0)
    Lebensdauer = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class KostenkennwerteLinienelemente(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    Euro_EH = Field(float, 0)
    Euro_EN = Field(float, 0)
    Cent_BU = Field(int, 0)
    Lebensdauer = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class Gesamtkosten(ProjectTable):
    IDNetz = Field(int, 0)
    Netz = Field(str, '')
    IDKostenphase = Field(int, 0)
    Kostenphase = Field(str, '')
    Euro = Field(float, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class Kostenaufteilung(ProjectTable):
    IDNetz = Field(int, 0)
    IDKostenphase = Field(int, 0)
    Anteil_GSB = Field(int, 0)
    Anteil_GEM = Field(int, 0)
    Anteil_ALL = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class GesamtkostenTraeger(ProjectTable):
    IDNetz = Field(int, 0)
    Netz = Field(str, '')
    Betrag_GSB = Field(float, 0)
    Betrag_GEM = Field(float, 0)
    Betrag_ALL = Field(float, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'

