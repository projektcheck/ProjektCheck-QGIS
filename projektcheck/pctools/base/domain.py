from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
import os

UI_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'ui')


class PCDockWidget(QtWidgets.QDockWidget):
    ui_file = None
    closingPlugin = pyqtSignal()

    def __init__(self, iface=None):
        super().__init__()
        self.iface = iface
        # look for file ui folder if not found
        ui_file = self.ui_file if os.path.exists(self.ui_file) \
            else os.path.join(UI_PATH, self.ui_file)
        uic.loadUi(ui_file, self)
        self.setupUi()

    def setupUi(self):
        pass

    def show(self, position=Qt.RightDockWidgetArea):
        self.iface.addDockWidget(position, self)

    def unload(self):
        print('removing {}'.format(str(self)))
        self.iface.removeDockWidget(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


class Domain(PCDockWidget):
    '''
    area of ​​knowledge with settings and tools, displayed in seperate dock widget
    '''
    label = None

    #def show(self, parent):
        #pass

    def connect(self):
        pass


