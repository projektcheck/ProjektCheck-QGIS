from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
import os

UI_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'ui')


class PCDockWidget(QtWidgets.QDockWidget):
    ui_file = None
    closingPlugin = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, self.ui_file), self)
        self.setupUi()

    def setupUi(self):
        raise NotImplementedError

    def show(self, iface=None, position=Qt.RightDockWidgetArea):
        print(iface)
        print(os.path.join(UI_PATH, self.ui_file))
        iface.addDockWidget(position, self)

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


