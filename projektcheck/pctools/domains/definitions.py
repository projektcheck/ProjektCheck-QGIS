from pctools.base import (Domain, ParamView, Param, Slider, SpinBox,
                          Title, Seperator)
from pctools.backend import Geopackage


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projekt-Definitionen'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'

    def setupUi(self):
        for area in self.project.areas:
            self.ui.area_combo.addItem(area)
        self.ui.area_combo.currentTextChanged.connect(self.change_area)
        self.workspace = self.database.get_workspace('Definition')
        print(self.database)

        # ToDo: take from database
        for typ in ['Wohnen', 'Gewerbe', 'Einzelhandel']:
            self.ui.type_combo.addItem(typ)
        self.ui.type_combo.currentTextChanged.connect(self.change_type)
        self.param_view = None
        self.setup_living()

    def change_area(self, area):
        pass

    def change_type(self, typ):
        if self.param_view:
            self.param_view.close()

    def setup_living(self):
        table = self.workspace.get_table('Wohnen_Struktur_und_Alterung')
        self.param_view = ParamView()
        begin = Param(0, Slider(), label='Beginn des Bezuges')
        period = Param(0, SpinBox(), label='Dauer des Bezuges')

        self.param_view.add(Title('Bezugszeitraum'))
        self.param_view.add(begin)
        self.param_view.add(period)
        self.param_view.add(Seperator())

        self.param_view.show(self.ui.param_layout)

    def save_living(self):
        pass

    def setup_industry(self):
        pass

    def setup_retail(self):
        pass
