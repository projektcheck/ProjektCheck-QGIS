from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
import os

from pctools.base.project import ProjectManager

UI_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'ui')


class PCDockWidget(QtWidgets.QDockWidget):
    ui_file = None
    closingPlugin = pyqtSignal()
    project_manager = ProjectManager()

    def __init__(self, iface=None, position=Qt.RightDockWidgetArea):
        super().__init__()
        print(self.project)
        self.iface = iface
        self.initial_position = position
        # look for file ui folder if not found
        ui_file = self.ui_file if os.path.exists(self.ui_file) \
            else os.path.join(UI_PATH, self.ui_file)
        uic.loadUi(ui_file, self)
        #self.setAllowedAreas(
            #Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea |
            #Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
        #)
        self.isActive = False
        self.setupUi()

    def setupUi(self):
        pass

    def show(self):
        if self.isActive:
            super().show()
            return
        self.iface.addDockWidget(self.initial_position, self)
        self.isActive = True

    def unload(self):
        print('removing {}'.format(str(self)))
        self.isActive = False
        self.iface.removeDockWidget(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    @property
    def project(self):
        return self.project_manager.active_project

    @property
    def config(self):
        return self.project_manager.config


class Domain(PCDockWidget):
    '''
    area of ​​knowledge with settings and tools, displayed in seperate dock widget
    '''
    label = None

    def __init__(self, iface=None, position=Qt.RightDockWidgetArea):
        super().__init__(iface=iface, position=position)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

    #def show(self, parent):
        #pass

    def connect(self):
        pass


