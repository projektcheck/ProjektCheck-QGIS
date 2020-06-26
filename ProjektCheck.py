# -*- coding: utf-8 -*-
'''
***************************************************************************
    ProjektCheck.py
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

class to load the plugin into the QGIS UI
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis import utils

# init resources
from projektchecktools.ui.resources_rc import *
from main_widget import ProjektCheckControl


class ProjektCheck:
    '''
    land-use planning for urban and rural development
    '''

    def __init__(self, iface=None):
        self.iface = iface or utils.iface
        self.toolbar = self.iface.addToolBar('Projekt-Check')
        self.toolbar.setObjectName('Projekt-Check')

        self.actions = []
        self.menu = 'Projekt-Check'

        self.pluginIsActive = False
        self.mainwidget = None
        self.drawwidget = None
        self.toolbuttonwidget = None

    def initGui(self):
        '''
        override, add entry points (actions) for the plugin
        '''

        icon_path = ':/images/images/icon.png'
        icon = QIcon(icon_path)
        action = QAction(icon, 'Projekt-Check', self.iface.mainWindow())
        action.triggered.connect(lambda: self.run())
        self.toolbar.addAction(action)
        self.iface.addPluginToMenu('Geokodierung', action)

    def onClosePlugin(self):
        '''
        override, close UI on closing plugin
        '''

        # disconnects
        self.mainwidget.closing_widget.disconnect(self.onClosePlugin)
        self.mainwidget.close()

        self.pluginIsActive = False

    def unload(self):
        '''
        remove the plugin and its UI from the QGIS interface
        '''

        for action in self.actions:
            self.iface.removePluginMenu('Projekt-Check', action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        if self.toolbar:
            del self.toolbar
        # remove widget
        if self.mainwidget:
            self.mainwidget.close()
            self.mainwidget.unload()
            self.mainwidget.deleteLater()
            self.mainwidget = None
        self.pluginIsActive = False

    def run(self):
        '''
        open the plugin UI
        '''
        if self.pluginIsActive:
            return

        # initialize and show main widget
        if not self.mainwidget:
            # Create the dockwidget (after translation) and keep reference
            self.mainwidget = ProjektCheckControl(
                iface=self.iface, position=Qt.TopDockWidgetArea)

        # connect to provide cleanup on closing of dockwidget
        self.mainwidget.closing_widget.connect(self.onClosePlugin)

        # show the dockwidget
        self.mainwidget.show()


