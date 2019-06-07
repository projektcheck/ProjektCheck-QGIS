from pctools.base import Domain, Params


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projekt-Definitionen'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'
    workspace = 'Definition_Projekt'

    def setupUi(self):
        for area in self.project.areas:
            self.ui.area_combo.addItem(area)
        #self.setup_parameters()

    #def setup_parameters(self):
        #period = Params(self.workspace, table, label='Bezugszeitraum')
        #period = Params(self.workspace, table, label='Bezugszeitraum')
        #period = Params(self.workspace, table, label='Bezugszeitraum')
