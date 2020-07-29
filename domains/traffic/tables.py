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

project database tables of the traffic domain
'''

__author__ = 'Christoph Franke'
__date__ = '13/09/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class Connectors(ProjectTable):
    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')

    class Meta:
        workspace = 'traffic'


class Ways(ProjectTable):
    nutzungsart = Field(int, 0)
    miv_anteil = Field(float, 0)
    wege_gesamt = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class TrafficLoadLinks(ProjectTable):
    trips = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class RouteLinks(ProjectTable):
    from_node_id = Field(int, 0)
    to_node_id = Field(int, 0)
    transfer_node_id = Field(int, 0)
    area_id = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class Itineraries(ProjectTable):
    transfer_node_id = Field(int, 0)
    route_id = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class TransferNodes(ProjectTable):
    node_id = Field(int, 0)
    weight = Field(float, 0)
    name = Field(str, '')

    class Meta:
        workspace = 'traffic'



