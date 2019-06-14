from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt, QObject
import os

from pctools.base.project import ProjectManager

UI_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'ui')


class PCDockWidget(QObject):
    ui_file = None
    closingPlugin = pyqtSignal()

    def __init__(self, iface=None, position=Qt.RightDockWidgetArea):
        super().__init__()
        self.project_manager = ProjectManager()
        self.iface = iface
        self.initial_position = position
        self.ui = QtWidgets.QDockWidget()
        # look for file ui folder if not found
        ui_file = self.ui_file if os.path.exists(self.ui_file) \
            else os.path.join(UI_PATH, self.ui_file)
        uic.loadUi(ui_file, self.ui)
        #self.ui.setAllowedAreas(
            #Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea |
            #Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
        #)
        self.ui.closeEvent = self.closeEvent
        self.isActive = False
        self.setupUi()

    def setupUi(self):
        pass

    def close(self):
        self.ui.close()

    def show(self):
        if self.isActive:
            self.ui.show()
            return
        self.iface.addDockWidget(self.initial_position, self.ui)
        self.isActive = True

    def unload(self):
        self.isActive = False
        self.iface.removeDockWidget(self.ui)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    @property
    def project(self):
        return self.project_manager.active_project

    @property
    def settings(self):
        return self.project_manager.settings

    @property
    def database(self):
        return self.settings.DATABASE


class Domain(PCDockWidget):
    '''
    area of ​​knowledge with settings and tools, displayed in seperate dock widget
    '''
    label = None

    def __init__(self, iface=None, position=Qt.RightDockWidgetArea):
        super().__init__(iface=iface, position=position)
        self.ui.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

    #def show(self, parent):
        #pass

    def connect(self):
        pass


