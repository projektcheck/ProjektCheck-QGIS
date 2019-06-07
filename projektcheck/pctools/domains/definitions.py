from pctools.base import Domain, Params


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projekt-Definitionen'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'
    workspace = 'Definition_Projekt'

    def setupUi(self):
        if not self.project:
            self.close()
            return
        for area in self.project.areas:
            print(area)
