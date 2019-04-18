from qgis.PyQt import QtGui, QtWidgets, uic


class Domain(QtWidgets.QDockWidget):
    '''
    area of ​​knowledge with settings and tools, displayed in seperate dock widget
    '''
    ui_file = None
    label = None

    def __init__(self, workspace, ):
        QtWidgets.QDockWidget.__init__(self)
        uic.loadUi(os.path.join(
            os.path.dirname(__file__), 'testwidget.ui'), self)
        self.workspace = workspace

    def show(self, parent):
        pass

    def remove(self, parent):
        pass

    def connect(self):
        pass

