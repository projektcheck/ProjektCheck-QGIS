from pctools.base import Domain, ParamView
from pctools.backend import Geopackage

database = Geopackage()


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projekt-Definitionen'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'
    workspace = database.get_workspace('Definitions')

    def setupUi(self):
        for area in self.project.areas:
            self.ui.area_combo.addItem(area)
        self.ui.area_combo.currentTextChanged.connect(self.change_area)

        # ToDo: take from database
        for typ in ['Wohnen', 'Gewerbe', 'Einzelhandel']:
            self.ui.type_combo.addItem(typ)
        self.ui.type_combo.currentTextChanged.connect(self.change_type)

        #self.setup_parameters()

    def change_area(self, area):
        pass

    def change_type(self, typ):
        pass

    def setup_living(self):
        #period = Params(self.workspace, table, label='Bezugszeitraum')
        pass

    def setup_industry(self):
        pass

    def setup_retail(self):
        pass
