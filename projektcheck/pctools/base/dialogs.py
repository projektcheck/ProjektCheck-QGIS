from qgis.PyQt import uic
from qgis.PyQt.Qt import QDialog
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

class ParamsDialog(Dialog):
    ui_file = 'parameter_dialog.ui'

    def __init__(self, params):
        super().__init__(self.ui_file, modal=True)
        for param in params:
            param.show(self.param_layout)
