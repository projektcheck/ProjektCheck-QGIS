from qgis.PyQt import uic
from qgis.PyQt.Qt import (QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout,
                          Qt, QLineEdit, QLabel, QPushButton, QSpacerItem,
                          QSizePolicy)
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel, QgsVectorLayer
import os

from projektcheck.base.domain import UI_PATH
from projektcheck.base.project import ProjectManager


class Dialog(QDialog):
    def __init__(self, ui_file=None, modal=True, parent=None):
        super().__init__(parent=parent)
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
    '''
    dialog showing the progress of a thread
    '''
    ui_file = None

    def __init__(self):
        pass

    def show(self):
        pass

    def message(self):
        pass

    def connect(self):
        pass

    def setupUi(self):
        pass


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

