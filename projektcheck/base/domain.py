from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt, QObject, QThread
from qgis import utils
import os

from projektcheck.base.project import ProjectManager

UI_PATH = os.path.join(os.path.dirname(__file__), os.pardir, 'ui')


class PCDockWidget(QObject):
    '''
    dock widget, can be rendered in QGIS

    Attributes
    ----------
    ui : QDockWidget
        the actual qwidget holding all child ui elements
    ui_file : str
        the qt ui file used for rendering the widget
    value : basic_type
        current value of the parameter
    closingWidget : pyqtSignal
        fired when widget is closed
    project : Project
        active project
    settings : Settings
        projekt-check related settings
    projectdata : Database,
        database of the active project
    basedata :
        database with all base data
    '''
    ui_file = None
    closingWidget = pyqtSignal()

    def __init__(self, iface=None, canvas=None, position=Qt.RightDockWidgetArea):
        '''
        Parameters
        ----------
        iface : QgisInterface
            instance of QGIS interface
        position : int, optional
            dock widget area to add widget to, by default Qt.RightDockWidgetArea
        '''
        super().__init__()
        self.project_manager = ProjectManager()
        self.iface = iface or utils.iface
        self.canvas = canvas or self.iface.mapCanvas()
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

    def setupUi(self):
        '''
        setup ui, called when widget is shown
        override in sub classes to setup the ui elements of the widget
        '''
        pass

    def close(self):
        self.isActive = False
        self.ui.close()

    def show(self):
        '''
        show the widget inside QGIS
        '''
        if self.isActive:
            self.ui.show()
            return
        self.setupUi()
        self.iface.addDockWidget(self.initial_position, self.ui)
        self.isActive = True

    def unload(self):
        '''
        unload the widget
        '''
        self.isActive = False
        self.close()
        self.iface.removeDockWidget(self.ui)

    def closeEvent(self, event):
        self.closingWidget.emit()
        event.accept()

    @property
    def project(self):
        return self.project_manager.active_project

    @property
    def settings(self):
        return self.project_manager.settings

    @property
    def projectdata(self):
        return self.project_manager.projectdata

    @property
    def basedata(self):
        return self.project_manager.basedata


class Domain(PCDockWidget):
    '''
    dock widget for specific area of ​​knowledge

    Attributes
    ----------
    label : str
        label for area of knowledge displayed in ui
    ui : QDockWidget
        the actual qwidget holding all child ui elements
    ui_file : str
        the qt ui file used for rendering the widget
    value : basic_type
        current value of the parameter
    closingWidget : pyqtSignal
        fired when widget is closed
    project : Project
        active project
    settings : Settings
        projekt-check related settings
    projectdata : Database,
        database of the active project
    basedata : Database,
        database with all base data
    '''
    ui_label = None
    ui_icon = ""

    def __init__(self, iface=None, canvas=None, position=Qt.RightDockWidgetArea):
        super().__init__(iface=iface, canvas=canvas, position=position)
        self.ui.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

    def connect(self):
        pass


class Worker(QThread):
    '''
    abstract worker
    '''

    # available signals to be used in the concrete worker
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    message = pyqtSignal(str)
    progress = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def run(self, on_success=None):
        '''
        runs code defined in self.work
        emits self.finished on success and self.error on exception

        Parameters
        ----------
        on_success : function
            function to executed on success
        '''
        try:
            result = self.work()
            self.finished.emit(result)
            if on_success:
                on_success()
        except Exception as e:
            self.error.emit(str(e))

    def work(self):
        '''
        override
        code to be executed when running worker

        Returns
        -------
        result : object
            result of work, emitted when code was run succesfully
        '''
        raise NotImplementedError

    def log(self, message):
        '''
        emits message

        Parameters
        ----------
        message : str
        '''
        print(message)
        self.message.emit(str(message))

    def set_progress(self, progress):
        '''
        emits progress

        Parameters
        ----------
        progress : int
            progress in percent, value in range [0, 100]
        '''
        self.progress.emit(progress)


