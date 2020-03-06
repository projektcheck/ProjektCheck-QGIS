from qgis.PyQt import uic
from qgis.PyQt.QtCore import QThread
from qgis.PyQt.Qt import (QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
                          Qt, QLineEdit, QLabel, QPushButton, QSpacerItem,
                          QSizePolicy, QTimer, QVariant, QTextCursor)
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg,
                                                NavigationToolbar2QT)
from qgis.utils import iface
import matplotlib.pyplot as plt

import os
import datetime

from projektchecktools.base.domain import UI_PATH
from projektchecktools.base.project import ProjectManager


class Dialog(QDialog):
    def __init__(self, ui_file=None, modal=True, parent=None, title=None):
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
        pass

    def show(self):
        return self.exec_()


class NewProjectDialog(Dialog):

    def setupUi(self):
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
        self.layer_combo.setCurrentIndex(-1)
        self.layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)

        self.source = None
        def set_layer(layer):
            status_text = ''
            if not layer:
                path = self.layer_combo.currentText()
                layer = QgsVectorLayer(path, 'testlayer_shp', 'ogr')
            if not layer.isValid():
                layer = None
                status_text = 'Der Layer ist ungültig.'
            self.status_label.setText(status_text)
            self.source = layer

        self.layer_combo.layerChanged.connect(set_layer)
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

    def browse_path(self):
        path, sf = QFileDialog.getOpenFileName(
            self, u'Datei wählen', filter="Shapefile(*.shp)",
            directory=self.path)
        if path:
            self.path = os.path.split(path)[0]
            self.layer_combo.setAdditionalItems([str(path)])
            self.layer_combo.selectedindex = self.layer_combo.count() - 1

    def show(self):
        confirmed = self.exec_()
        if confirmed:
            return confirmed, self.name_edit.text(), self.source
        return False, None, None

    def validate(self):
        name = str(self.name_edit.text())
        status_text = ''
        if name in self.project_names:
            status_text = (
                f'Ein Projekt mit dem Namen {name} existiert bereits!\n'
                'Projektnamen müssen einzigartig sein.')
            self.ok_button.setEnabled(False)
            self.status_label.setText(status_text)
            return
        self.status_label.setText(status_text)

        if name and self.source:
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)


class ProgressDialog(Dialog):
    """
    Dialog showing progress in textfield and bar after starting a certain task with run()
    """
    ui_file = 'progress.ui'

    def __init__(self, worker, on_success=None,
                 parent=None, auto_close=False, auto_run=True,
                 on_close=None):
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

        self.worker = worker
        self.worker.finished.connect(self._success)
        self.worker.error.connect(self.on_error)
        self.worker.message.connect(self.show_status)
        self.worker.progress.connect(self.progress)

        self.start_button.clicked.connect(self.run)
        self.stop_button.clicked.connect(self.stop)
        self.close_button.clicked.connect(self.close)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)


    def show(self):
        QDialog.show(self)
        if self.auto_run:
            self.run()

    def _success(self, result):
        self._finished()
        self.progress(100)
        self.show_status('<br><b>fertig</b>')
        if not self.error:
            self.success = True
            if self.on_success:
                self.on_success(result)

    def _finished(self):
        #self.worker.deleteLater()
        self.timer.stop()
        self.close_button.setVisible(True)
        self.close_button.setEnabled(True)
        self.stop_button.setVisible(False)
        if self.auto_close_check.isChecked() and not self.error:
            self.close()

    def close(self):
        super().close()
        if self.on_close:
            self.on_close(self.on_close)

    def on_error(self, message):
        self.show_status( f'<span style="color:red;">Fehler: {message}</span>')
        self.progress_bar.setStyleSheet(
            'QProgressBar::chunk { background-color: red; }')
        self.error = True
        self._finished()

    def show_status(self, text):
        self.log_edit.appendHtml(text)
        #self.log_edit.moveCursor(QTextCursor.Down)
        scrollbar = self.log_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum());

    def progress(self, progress, obj=None):
        if isinstance(progress, QVariant):
            progress = progress.toInt()[0]
        self.progress_bar.setValue(progress)

    def start_timer(self):
        self.start_time = datetime.datetime.now()
        self.timer.start(1000)

    # task needs to be overridden
    def run(self):
        self.error = False
        self.start_timer()
        self.stop_button.setVisible(True)
        self.start_button.setVisible(False)
        self.close_button.setVisible(True)
        self.close_button.setEnabled(False)
        self.worker.start()

    def stop(self):
        self.timer.stop()
        self.worker.terminate()
        self.log_edit.appendHtml('<b> Vorgang abgebrochen </b> <br>')
        self.log_edit.moveCursor(QTextCursor.End)
        self._finished()

    def update_timer(self):
        delta = datetime.datetime.now() - self.start_time
        h, remainder = divmod(delta.seconds, 3600)
        m, s = divmod(remainder, 60)
        timer_text = '{:02d}:{:02d}:{:02d}'.format(h, m, s)
        self.elapsed_time_label.setText(timer_text)


class SettingsDialog(Dialog):
    '''changes settings in place'''
    ui_file = 'settings.ui'

    def __init__(self, settings):
        super().__init__(self.ui_file, modal=True)
        self.settings = settings
        self.project_browse_button.clicked.connect(
            lambda: self.browse_path(self.project_path_edit))
        self.basedata_browse_button.clicked.connect(
            lambda: self.browse_path(self.basedata_path_edit))

    def browse_path(self, line_edit):
        path = str(
            QFileDialog.getExistingDirectory(
                self,
                u'Verzeichnis wählen',
                line_edit.text()
            )
        )
        if not path:
            return
        line_edit.setText(path)

    def show(self):
        self.project_path_edit.setText(self.settings.project_path)
        self.basedata_path_edit.setText(self.settings.basedata_path)
        self.check_on_start.setChecked(self.settings.check_data_on_start)
        confirmed = self.exec_()
        if confirmed:
            project_path = self.project_path_edit.text()
            if not os.path.exists(project_path):
                try:
                    os.makedirs(project_path)
                except:
                    # ToDo: show warning that it could not be created
                    return
            self.project_path = project_path
            return self.project_path
        else:
            self.project_path_edit.setText(self.project_path)
        return confirmed


class DiagramDialog(Dialog):

    def __init__(self, figure, title='Diagramm', modal=False):
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

    def show(self, offset_x=0, offset_y=0):
        #subplot.set_axis_off()
        plt.gcf().canvas.draw_idle()
        self.adjustSize()
        QDialog.show(self)
        if offset_x or offset_y:
            geometry = self.geometry()
            self.setGeometry(geometry.x() + offset_x, geometry.y() + offset_y,
                             geometry.width(), geometry.height())
