# -*- coding: utf-8 -*-
'''
***************************************************************************
    tables.py
    ---------------------
    Date                 : October 2019
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

project database tables holding job and population development
'''

__author__ = 'Christoph Franke'
__date__ = '14/10/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class ApProJahr(ProjectTable):

    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')
    jahr = Field(int, 0)
    arbeitsplaetze = Field(int, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'


class WohnenStruktur(ProjectTable):

    id_teilflaeche = Field(int, 0)
    jahr = Field(int, 0)
    alter_we = Field(int, 0)
    id_gebaeudetyp = Field(int, 0)
    wohnungen = Field(float, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'


class WohnenProJahr(ProjectTable):

    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')
    jahr = Field(int, 0)
    id_altersklasse = Field(int, 0)
    altersklasse = Field(str, '')
    bewohner = Field(float, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'
