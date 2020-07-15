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

project database tables of ecology domain
'''

__author__ = 'Christoph Franke'
__date__ = '10/01/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class BodenbedeckungNullfall(ProjectTable):

    IDBodenbedeckung = Field(int, 0)
    area = Field(float, 0)

    class Meta:
        workspace = 'oekologie'


class BodenbedeckungPlanfall(ProjectTable):

    IDBodenbedeckung = Field(int, 0)
    area = Field(float, 0)

    class Meta:
        workspace = 'oekologie'


class BodenbedeckungAnteile(ProjectTable):

    IDBodenbedeckung = Field(int, 0)
    planfall = Field(bool, True)
    anteil = Field(int, 0)

    class Meta:
        workspace = 'oekologie'
