# -*- coding: utf-8 -*-
'''
***************************************************************************
    tables.py
    ---------------------
    Date                 : January 2020
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

project database tables of landuse
'''

__author__ = 'Christoph Franke'
__date__ = '22/01/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class WohnbaulandAnteile(ProjectTable):

    id_teilflaeche = Field(int, 0)
    nettoflaeche = Field(float, 0)

    class Meta:
        workspace = 'definitions'


class WohnflaecheGebaeudetyp(ProjectTable):

    id_teilflaeche = Field(int, 0)
    mean_wohnflaeche = Field(int, 0)
    id_gebaeudetyp = Field(int, 0)
    name_gebaeudetyp = Field(str, 0)

    class Meta:
        workspace = 'definitions'


class GrenzeSiedlungskoerper(ProjectTable):

    class Meta:
        workspace = 'definitions'