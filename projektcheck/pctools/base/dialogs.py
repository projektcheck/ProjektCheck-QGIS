from qgis.PyQt import uic
from qgis.PyQt.Qt import QDialog
from qgis.PyQt.QtWidgets import QFileDialog
import os

from pctools.base.domain import UI_PATH


class Dialog(QDialog):
    def __init__(self, ui_file, modal=True, parent=None):
        super().__init__(parent=parent)
        # look for file ui folder if not found
        ui_file = ui_file if os.path.exists(ui_file) \
            else os.path.join(UI_PATH, ui_file)
        print(ui_file)
        uic.loadUi(ui_file, self)
        self.setModal(modal)
        self.setupUi()

    def setupUi(self):
        pass


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

