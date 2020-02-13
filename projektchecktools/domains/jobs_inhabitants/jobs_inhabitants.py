from projektchecktools.base.domain import Domain
from projektchecktools.domains.constants import Nutzungsart
from projektchecktools.domains.jobs_inhabitants.diagrams import (
    BewohnerEntwicklung, ArbeitsplatzEntwicklung, BranchenAnteile)
from projektchecktools.domains.definitions.tables import Teilflaechen
from projektchecktools.base.dialogs import DiagramDialog


class JobsInhabitants(Domain):
    """"""
    ui_label = 'Bewohner und Arbeitsplätze'
    ui_file = 'ProjektCheck_dockwidget_analysis_01-BA.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_people_1.png"

    def setupUi(self):
        self.ui.inhabitants_button.clicked.connect(self.inhabitants_diagram)
        self.ui.jobs_button.clicked.connect(self.jobs_diagram)

    def inhabitants_diagram(self):
        areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.WOHNEN.value)
        for area in areas:
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Einwohnerentwicklung")
            diagram = BewohnerEntwicklung(area=area, title=title)
            diagram.draw()

    def jobs_diagram(self):
        areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.GEWERBE.value)
        for area in areas:
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Anzahl Arbeitsplätze (Orientierungswerte)")
            diagram = ArbeitsplatzEntwicklung(area=area, title=title)
            diagram.draw()

            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Branchenanteile an den Arbeitsplätzen")
            diagram = BranchenAnteile(area=area, title=title)
            diagram.draw()
