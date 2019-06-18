# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import (QSettings, QTranslator, qVersion,
                              QCoreApplication, Qt)
from qgis.PyQt.QtGui import QIcon, QPixmap, QPalette, QBrush
from qgis.PyQt.QtWidgets import QAction

# Initialize Qt resources from file resources_rc.py
from pctools.ui.resources_rc import *

# Import the code for the DockWidget
from ProjektCheck_dockwidget import ProjektCheckMainDockWidget
import os.path


class ProjektCheck:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ProjektCheck_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Projekt-Check')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Projekt-Check')
        self.toolbar.setObjectName(u'Projekt-Check')

        #print "** INITIALIZING ProjektCheck"

        self.pluginIsActive = False
        self.mainwidget = None
        self.drawwidget = None
        self.toolbuttonwidget = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Projekt-Check', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/ProjektCheck/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Projekt-Check'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # disconnects
        self.mainwidget.closingWidget.disconnect(self.onClosePlugin)
        self.mainwidget.close()

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        print("** UNLOAD ProjektCheck")

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Projekt-Check'),
                action)
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

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""
        if self.pluginIsActive:
            return

        # initialize and show main widget
        if not self.mainwidget:
            # Create the dockwidget (after translation) and keep reference
            self.mainwidget = ProjektCheckMainDockWidget(
                iface=self.iface, position=Qt.TopDockWidgetArea)

        # connect to provide cleanup on closing of dockwidget
        self.mainwidget.closingWidget.connect(self.onClosePlugin)

        # show the dockwidget
        self.mainwidget.show()


