# -*- coding: utf-8 -*-
'''
***************************************************************************
    __init__.py
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

initializes the plugin, makes it known to QGIS
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

# debugging in WingIDE
try:
    import wingdbstub
    wingdbstub.Ensure()
except:
    pass

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    # initialize the settings
    from .settings import settings
    from .ProjektCheck import ProjektCheck
    return ProjektCheck(iface)
