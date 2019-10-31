from qgis.PyQt import uic
from qgis.PyQt.QtCore import QThread
from qgis.PyQt.Qt import (QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
                          Qt, QLineEdit, QLabel, QPushButton, QSpacerItem,
                          QSizePolicy, QTimer, QVariant, QTextCursor)
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg,
                                                NavigationToolbar2QT)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import os
import datetime

from projektcheck.base.domain import UI_PATH
from projektcheck.base.project import ProjectManager


class Dialog(QDialog):
    def __init__(self, ui_file=None, modal=True, parent=None, title=None):
        super().__init__(parent=parent)
        if title:
            self.setWindowTitle(title)

        if ui_file:
            # look for file ui folder if not found
            ui_file = ui_file if os.path.exists(ui_file) \
                else os.path.join(UI_PATH, ui_file)
            uic.loadUi(ui_file, self)
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

    def __init__(self, thread, on_success=None,
                 parent=None, auto_close=False, auto_run=True):
        super().__init__(self.ui_file, modal=True, parent=parent)
        self.parent = parent
        self.setupUi()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.progress_bar.setValue(0)
        self.close_button.clicked.connect(self.close)
        self.stop_button.setVisible(False)
        self.close_button.setVisible(False)
        self.auto_close = auto_close
        self.auto_run = auto_run
        self.on_success = on_success

        self.thread = thread
        self.thread.finished.connect(self.success)
        self.thread.error.connect(self.on_error)
        self.thread.message.connect(self.show_status)
        self.thread.progress.connect(self.progress)

        self.start_button.clicked.connect(self.run)
        self.stop_button.clicked.connect(self.stop)
        self.close_button.clicked.connect(self.close)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

    def show(self):
        QDialog.show(self)
        if self.auto_run:
            self.run()

    def success(self, result):
        self.finished()
        self.progress(100)
        self.show_status('<br>fertig')
        if self.on_success:
            self.on_success(result)

    def finished(self):
        #self.thread.quit()
        #self.thread.wait()
        #self.thread.deleteLater()
        self.timer.stop()
        self.close_button.setVisible(True)
        self.close_button.setEnabled(True)
        self.stop_button.setVisible(False)
        if self.auto_close:
            self.close()

    def on_error(self, message):
        self.show_status( f'<span style="color:red;">Fehler: {message}</span>')
        self.progress_bar.setStyleSheet(
            'QProgressBar::chunk { background-color: red; }')

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
        self.start_timer()
        self.stop_button.setVisible(True)
        self.start_button.setVisible(False)
        self.close_button.setVisible(True)
        self.close_button.setEnabled(False)
        self.thread.start()

    def stop(self):
        self.timer.stop()
        self.thread.terminate()
        self.log_edit.appendHtml('<b> Vorgang abgebrochen </b> <br>')
        self.log_edit.moveCursor(QTextCursor.End)
        self.finished()

    def update_timer(self):
        delta = datetime.datetime.now() - self.start_time
        h, remainder = divmod(delta.seconds, 3600)
        m, s = divmod(remainder, 60)
        timer_text = '{:02d}:{:02d}:{:02d}'.format(h, m, s)
        self.elapsed_time_label.setText(timer_text)


class Message:
    '''
    dialog showing a message
    '''


class SettingsDialog(Dialog):
    ui_file = 'settings.ui'

    def __init__(self, project_path):
        super().__init__(self.ui_file, modal=True)
        self.project_path = project_path
        self.browse_button.clicked.connect(self.browse_path)

    def browse_path(self):
        path = str(
            QFileDialog.getExistingDirectory(
                self,
                u'Verzeichnis wählen',
                self.project_path_edit.text()
            )
        )
        if not path:
            return
        self.project_path_edit.setText(path)

    def show(self):
        self.project_path_edit.setText(self.project_path)
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

    def show(self):
        #subplot.set_axis_off()
        plt.gcf().canvas.draw_idle()
        self.adjustSize()
        QDialog.show(self)
