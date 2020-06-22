from qgis.PyQt import uic
import re
from typing import Tuple, Union
from qgis.PyQt.Qt import (QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
                          Qt, QLineEdit, QLabel, QPushButton, QSpacerItem,
                          QSizePolicy, QTimer, QVariant, QTextCursor, QObject)
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QWidget
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer, QgsWkbTypes
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg,
                                                NavigationToolbar2QT)
import matplotlib.pyplot as plt
from zipfile import ZipFile, BadZipFile
import os
import datetime
from io import BytesIO
import shutil
from time import sleep

from projektchecktools.base.domain import UI_PATH, Worker
from projektchecktools.base.project import ProjectManager
from projektchecktools.utils.connection import Request


class Dialog(QDialog):
    '''
    Dialog
    '''
    def __init__(self, ui_file: str = None, modal: bool = True,
                 parent: QWidget = None, title: str = None):
        '''
        Parameters
        ----------
        ui_file : str, optional
            path to QT-Designer xml file to load UI of dialog from,
            if only filename is given, the file is looked for in the standard
            folder (UI_PATH), defaults to not using ui file
        modal : bool, optional
            set dialog to modal if True, not modal if False, defaults to modal
        parent: QWidget, optional
            parent widget, defaults to None
        title: str, optional
            replaces title of dialog if given, defaults to preset title
        '''

        super().__init__(parent=parent)
        if ui_file:
            # look for file ui folder if not found
            ui_file = ui_file if os.path.exists(ui_file) \
                else os.path.join(UI_PATH, ui_file)
            uic.loadUi(ui_file, self)
        if title:
            self.setWindowTitle(title)
        self.setModal(modal)
        self.setupUi()

    def setupUi(self):
        '''
        override this to set up the user interface
        '''
        pass

    def show(self):
        '''
        override, show the dialog
        '''
        return self.exec_()


class NewProjectDialog(Dialog):
    '''
    dialog to select a layer and a name as inputs for creating a new project
    '''
    def setupUi(self):
        '''
        set up the user interface
        '''
        self.setMinimumWidth(500)
        self.setWindowTitle('Neues Projekt erstellen')

        project_manager = ProjectManager()
        self.project_names = [p.name for p in project_manager.projects]

        layout = QVBoxLayout(self)

        label = QLabel('Name des Projekts')
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.validate)
        layout.addWidget(label)
        layout.addWidget(self.name_edit)
        self.path = os.path.join(project_manager.settings.TEMPLATE_PATH,
                                 'projektflaechen')

        hlayout = QHBoxLayout(self)
        label = QLabel('Import der (Teil-)Flächen des Plangebiets')
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)

        self.source = None

        self.layer_combo.layerChanged.connect(self.set_layer)
        self.layer_combo.layerChanged.connect(self.validate)
        browse_button = QPushButton('...')
        browse_button.clicked.connect(self.browse_path)
        browse_button.setMaximumWidth(30)
        hlayout.addWidget(self.layer_combo)
        hlayout.addWidget(browse_button)
        layout.addWidget(label)
        layout.addLayout(hlayout)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        spacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.ok_button = buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if len(self.layer_combo) > 0:
            self.set_layer(self.layer_combo.currentLayer())
        self.layer_combo.setCurrentIndex(0)

    def set_layer(self, layer: QgsVectorLayer = None):
        '''
        set layer as user selection

        Parameters
        ----------
        layer : QgsVectorLayer
            the selected layer
        '''
        if not layer:
            path = self.layer_combo.currentText()
            layer = QgsVectorLayer(path, 'testlayer_shp', 'ogr')
        self.source = layer
        self.validate()

    def browse_path(self):
        '''
        open dialog for user input of path to a shapefile and add it to the
        layer-combo
        '''
        path, sf = QFileDialog.getOpenFileName(
            self, 'Datei wählen', filter="Shapefile(*.shp)",
            directory=self.path)
        if path:
            self.path = os.path.split(path)[0]
            self.layer_combo.setAdditionalItems([str(path)])
            self.layer_combo.setCurrentIndex(self.layer_combo.count()-1)
            self.set_layer()

    def show(self) -> Tuple[bool, str, QgsVectorLayer]:
        '''
        show dialog and return selections made by user
        '''
        confirmed = self.exec_()
        if confirmed:
            return confirmed, self.name_edit.text(), self.source
        return False, None, None

    def validate(self):
        '''
        validate current input of name and layer, set the status label according
        to validation result
        '''
        name = str(self.name_edit.text())
        status_text = ''
        regexp = re.compile(f'[\\\/\:*?\"\'<>|]')
        error = False
        if name and regexp.search(name):
            status_text = ('Der Projektname darf keines der folgenden Zeichen '
                           f'enthalten: \/:*?"\'<>|')
            error = True
        elif name in self.project_names:
            status_text = (
                f'Ein Projekt mit dem Namen {name} existiert bereits!\n'
                'Projektnamen müssen einzigartig sein.')
            error = True

        if self.source:
            if not self.source.isValid():
                status_text = 'Der Layer ist ungültig.'
                error = True
            elif not self.source.geometryType() == QgsWkbTypes.PolygonGeometry:
                status_text = 'Der Layer hat keine Polygongeometrie.'
                error = True

        self.status_label.setText(status_text)

        if not error and (name and self.source):
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)


class ProgressDialog(Dialog):
    '''
    Dialog showing progress in textfield and a progress bar after starting a
    certain task with run(). Contains a log section and a timer

    Attributes
    ----------
    success : bool
        indicates if the task was run successfully without errors
    error : bool
        indicates if an error occured while running the task
    '''
    ui_file = 'progress.ui'

    def __init__(self, worker: Worker, parent: QObject = None,
                 auto_close: bool = False, auto_run: bool = True,
                 on_success: object = None, on_close: object = None):
        '''
        Parameters
        ----------
        worker : Worker
            Worker object holding the task to do
        parent : QObject, optional
            parent ui element of the dialog, defaults to no parent
        auto_close : bool, optional
            close dialog automatically after task is done, defaults to automatic
            close
        auto_run : bool, optional
            start task automatically when showing the dialog, otherwise the user
            has to start it by pressing the start-button, defaults to automatic
            start
        on_success : object, optional
            function to call on successful run of task, function has to expect
            the result of the task as an argument, defaults to no callback on
            success
        on_close : object, optional
            function to call when closing the dialog, defaults to no callback on
            closing
        '''
        # parent = parent or iface.mainWindow()
        super().__init__(self.ui_file, modal=True, parent=parent)
        self.parent = parent
        self.setupUi()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.progress_bar.setValue(0)
        self.stop_button.setVisible(False)
        self.close_button.setVisible(False)
        self.auto_close_check.setChecked(auto_close)
        self.auto_run = auto_run
        # ToDo: use signals instead of callbacks
        self.on_success = on_success
        self.on_close = on_close
        self.success = False
        self.error = False

        self.worker = worker
        if self.worker:
            self.worker.finished.connect(self._success)
            self.worker.error.connect(self.on_error)
            self.worker.message.connect(self.show_status)
            self.worker.progress.connect(self.progress)

        self.start_button.clicked.connect(self.run)
        self.stop_button.clicked.connect(self.stop)
        self.close_button.clicked.connect(self.close)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)

    def show(self):
        '''
        show the dialog
        '''
        QDialog.show(self)
        if self.auto_run:
            self.run()

    def _success(self, result: object = None):
        '''
        handle successful run
        '''
        self.progress(100)
        self.show_status('<br><b>fertig</b>')
        if not self.error:
            self.success = True
            if self.on_success:
                self.on_success(result)
        self._finished()

    def _finished(self):
        '''
        handle finished run
        '''
        #self.worker.deleteLater()
        self.timer.stop()
        self.close_button.setVisible(True)
        self.close_button.setEnabled(True)
        self.stop_button.setVisible(False)
        if self.auto_close_check.isChecked() and not self.error:
            self.close()

    def close(self):
        '''
        close the dialog
        '''
        super().close()
        if self.on_close:
            self.on_close()

    def on_error(self, message: str):
        '''
        call this if error occurs while running task

        Parameters
        ----------
        message : str
            error message to show
        '''
        self.show_status( f'<span style="color:red;">Fehler: {message}</span>')
        self.progress_bar.setStyleSheet(
            'QProgressBar::chunk { background-color: red; }')
        self.error = True
        self._finished()

    def show_status(self, text: str):
        '''
        write message into the log section

        Parameters
        ----------
        text : str
            message to show
        '''
        self.log_edit.appendHtml(text)
        #self.log_edit.moveCursor(QTextCursor.Down)
        scrollbar = self.log_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum());

    def progress(self, progress: Union[int, QVariant]):
        '''
        set progress of task

        Parameters
        ----------
        progress : int or QVariant
            progress in percent [0..100]
        '''
        if isinstance(progress, QVariant):
            progress = progress.toInt()[0]
        self.progress_bar.setValue(progress)

    def start_timer(self):
        '''
        start the timer
        '''
        self.start_time = datetime.datetime.now()
        self.timer.start(1000)

    def run(self):
        '''
        run the task
        '''
        self.error = False
        self.start_timer()
        self.stop_button.setVisible(True)
        self.start_button.setVisible(False)
        self.close_button.setVisible(True)
        self.close_button.setEnabled(False)
        if self.worker:
            self.worker.start()

    def stop(self):
        '''
        cancel the task
        '''
        self.timer.stop()
        if self.worker:
            self.worker.terminate()
        self.log_edit.appendHtml('<b> Vorgang abgebrochen </b> <br>')
        self.log_edit.moveCursor(QTextCursor.End)
        self._finished()

    def _update_timer(self):
        '''
        update the timer
        '''
        delta = datetime.datetime.now() - self.start_time
        h, remainder = divmod(delta.seconds, 3600)
        m, s = divmod(remainder, 60)
        timer_text = '{:02d}:{:02d}:{:02d}'.format(h, m, s)
        self.elapsed_time_label.setText(timer_text)


class SettingsDialog(Dialog):
    '''
    dialog to set up the plugin
    '''
    ui_file = 'settings.ui'

    def __init__(self, control: 'ProjektCheckControl'):
        '''
        Parameters
        ----------
        control : ProjektCheckControl
            the main widget controlling the projects and domains
        '''
        super().__init__(self.ui_file, modal=True)
        self.control = control
        self.project_manager = ProjectManager()
        self.settings = self.project_manager.settings

        self.project_browse_button.clicked.connect(
            lambda: self.browse_path(self.project_path_edit))
        self.basedata_browse_button.clicked.connect(
            lambda: self.browse_path(self.basedata_path_edit))
        self.basedata_path_edit.textChanged.connect(
            self.check_basedata_path)

        self.download_button.clicked.connect(self.download_basedata)
        self.ok_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)

        self.project_path_edit.setText(self.settings.project_path)
        self.basedata_path_edit.setText(self.settings.basedata_path)
        self.check_on_start.setChecked(self.settings.check_data_on_start)
        self.check_basedata_path()

    def download_basedata(self, version: int = None):
        '''
        download base data from server and store it in the path set by user

        Parameters
        ----------
        version : int, optional
            version of base data to download, defaults to newest version
            available
        '''
        base_path = self.basedata_path_edit.text()
        if not self.check_permission(base_path):
            return
        self.control.close_all_projects()
        server_versions = self.project_manager.server_versions
        sv = [v['version'] for v in server_versions]
        if not version:
            # newest version
            version = sv[0]
        idx = sv.index(version)
        # ToDo: version not on server
        v = server_versions[idx]
        url = f'{self.settings.BASEDATA_URL}/{v["file"]}'
        # put data in subfolder (named after version)
        path = os.path.join(base_path, str(version))

        def on_success(a):
            self.project_manager.add_local_version(v)
            self.check_basedata_path()

        def on_close():
            if self.download_dialog.permission_error:
                QMessageBox.warning(
                    self, 'Hinweis',
                    'Beim Speichern der Basisdaten ist ein Fehler aufgetreten.'
                    '\n\nMöglicherweise konnten die alten Daten nicht restlos '
                    'entfernt werden. Bitte starten Sie QGIS neu und versuchen '
                    'Sie den Download erneut (ohne geöffnete Projekte).')
                self.check_basedata_path()

        self.download_dialog = DownloadDialog(
            url, path, parent=self, on_success=on_success,
            auto_close=True, on_close=on_close)
        self.download_dialog.show()

    def check_basedata_path(self):
        '''
        validate the local base data
        '''
        path = self.basedata_path_edit.text()
        valid, status_text = self.project_manager.check_basedata(path)
        color = 'green' if valid == 2 else 'black' if valid == 1 else 'red'
        self.download_button.setEnabled(False if valid == -1 else True)
        self.status_label.setStyleSheet(f'color: {color};')
        self.status_label.setText(status_text)

    def browse_path(self, line_edit: QLineEdit):
        '''
        open a dialog for user input of a path and write it into the given edit

        Parameters
        ----------
        line_edit : QLineEdit
            the line edit to set the user input to
        '''
        path = str(
            QFileDialog.getExistingDirectory(
                self,
                'Verzeichnis wählen',
                line_edit.text()
            )
        )
        if not path:
            return
        line_edit.setText(path)

    def check_permission(self, path: str):
        '''
        check write access to given path, create path if not existing

        Parameters
        ----------
        path : str
            the path to check
        '''
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            # ToDo: might not work for paths? always returns True for me
            if not os.access(path, os.X_OK | os.W_OK):
                raise PermissionError()
            return True
        except PermissionError:
            QMessageBox.warning(
                self, 'Warnung',
                f'Sie haben keine Zugriffsrechte auf den Pfad \n{path}\n'
                'Bitte wählen Sie einen anderen Pfad.'
            )
            return False

    def save(self):
        '''
        write the user inputs into the settings file
        '''
        project_path = self.project_path_edit.text()
        basedata_path = self.basedata_path_edit.text()
        for path in [project_path, basedata_path]:
            if not self.check_permission(path):
                return
        self.settings.project_path = project_path
        self.settings.basedata_path = basedata_path
        self.settings.check_data_on_start = self.check_on_start.isChecked()
        self.accept()


class DiagramDialog(Dialog):
    '''
    display a matplotlib plot in a dialog
    '''
    def __init__(self, figure: 'Figure', title: str = 'Diagramm',
                 modal: bool = False):
        '''
        Parameters
        ----------
        figure : Figure
            the matplotlib figure to display
        title : str, optional
            the title of the dialog, defaults to 'Diagramm'
        modal : bool, optional
            the modality of the dialog (modal if True, modeless if False),
            defaults to being modal
        '''
        super().__init__(modal=modal, title=title)
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvasQTAgg(figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def show(self, offset_x: int = 0, offset_y: int = 0):
        '''
        show the dialog

        Parameters
        ----------
        offset_x: int, optional
            offset of dialog position on the x-axis by this amount in pixels,
            defaults to no offset
        offset_y: int, optional
            offset of dialog position on the y-axis by this amount in pixels,
            defaults to no offset
        '''
        #subplot.set_axis_off()
        plt.gcf().canvas.draw_idle()
        self.adjustSize()
        QDialog.show(self)
        if offset_x or offset_y:
            geometry = self.geometry()
            self.setGeometry(geometry.x() + offset_x, geometry.y() + offset_y,
                             geometry.width(), geometry.height())


class DownloadDialog(ProgressDialog):
    '''
    dialog for downloading a file from an url
    '''
    def __init__(self, url, path, **kwargs):
        '''
        Parameters
        ----------
        url : str
            url of file to download
        path : str
            path to download file to
        parent : QObject, optional
            parent ui element of the dialog, defaults to no parent
        auto_close : bool, optional
            close dialog automatically after task is done, defaults to automatic
            close
        auto_run : bool, optional
            start download automatically when showing the dialog,
            defaults to automatic start
        on_success : object, optional
            function to call on successful download, function has to expect
            one argument (will always be None out of lazyness), defaults to no
            callback on success
        on_close : object, optional
            function to call when closing the dialog, defaults to no callback on
            closing
        '''
        super().__init__(None, **kwargs)
        self.url = url
        self.path = path

    def run(self):
        '''
        start the download
        '''
        self.permission_error = False
        self.status_code = 0
        self.stop_button.setVisible(False)
        self.start_button.setVisible(False)
        self.close_button.setVisible(True)
        self.close_button.setEnabled(False)

        self.show_status('Starte Download von')
        self.show_status(self.url)
        self.start_timer()
        try:
            request = Request(synchronous=False)
            request.progress.connect(self.progress)
            request.finished.connect(self._save)
            request.error.connect(self.on_error)
            request.get(self.url)
        except Exception as e:
            self.on_error(str(e))

    def _save(self, reply):
        '''
        save the reply of the server to the given path
        '''
        self.status_code = reply.status_code
        if reply.status_code != 200:
            self.on_error(reply.status_code)
            return
        self.show_status(f'-> {self.path}')
        # ToDo: catch errors (file permission->message to restart)
        try:
            if os.path.exists(self.path):
                shutil.rmtree(self.path, ignore_errors=False, onerror=None)
                sleep(1)
            os.makedirs(self.path)
            with ZipFile(BytesIO(reply.raw_data)) as zf:
                zf.extractall(self.path)
            self._success()
        except PermissionError as e:
            self.permission_error = True
            self.on_error('Zugriffsfehler: Alte Daten konnten nicht restlos '
                          'entfernt werden.')
        except BadZipFile as e:
            self.on_error(str(e))




