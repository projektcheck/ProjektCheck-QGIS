from projektcheck.base.domain import Domain
from projektcheck.domains.constants import Nutzungsart
from projektcheck.domains.jobs_inhabitants.diagrams import BewohnerEntwicklung
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.base.dialogs import DiagramDialog


class JobsInhabitants(Domain):
    """"""
    ui_label = 'Bewohner und Arbeitsplätze'
    ui_file = 'ProjektCheck_dockwidget_analysis_01-BA.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_people_1.png"

    def setupUi(self):
        self.ui.inhabitants_button.clicked.connect(self.bewohner_diagram)

    def bewohner_diagram(self):
        areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.WOHNEN.value)
        for area in areas:
            title = (f"{self.project.name} - {area.name}: "
                          "Geschätzte Einwohnerentwicklung")
            diagram = BewohnerEntwicklung(area=area, title=title)
            diagram.draw()
