import os
from qgis.PyQt.QtWidgets import QMessageBox

from projektchecktools.base.domain import Domain
from projektchecktools.domains.constants import Nutzungsart
from projektchecktools.domains.jobs_inhabitants.diagrams import (
    BewohnerEntwicklung, ArbeitsplatzEntwicklung, BranchenAnteile)
from projektchecktools.domains.definitions.tables import Teilflaechen
from projektchecktools.utils.utils import open_file


class JobsInhabitants(Domain):
    """"""
    ui_label = 'Bewohner und Arbeitsplätze'
    ui_file = 'ProjektCheck_dockwidget_analysis_01-BA.ui'
    ui_icon = 'images/iconset_mob/20190619_iconset_mob_people_1.png'
    layer_group = 'Wirkungsbereich 1 - Bewohner und Arbeitsplätze'

    def setupUi(self):
        self.ui.inhabitants_button.clicked.connect(self.inhabitants_diagram)
        self.ui.jobs_button.clicked.connect(self.jobs_diagram)

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Bewohner_und_Arbeitsplätze.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

    def inhabitants_diagram(self):
        areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.WOHNEN.value,
            we_gesamt__gt=0
        )
        if len(areas) == 0:
            QMessageBox.warning(
                self.ui, 'Bewohner',
                'Es wurden keine Teilflächen mit definierter '
                'Wohnnutzung gefunden'
            )
        for area in areas:
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Einwohnerentwicklung")
            diagram = BewohnerEntwicklung(area=area, title=title)
            diagram.draw()

    def jobs_diagram(self):
        areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.GEWERBE.value,
            ap_gesamt__gt=0
        )
        if len(areas) == 0:
            QMessageBox.warning(
                self.ui, 'Arbeitsplätze',
                'Es wurden keine Teilflächen mit definierter '
                'Gewerbenutzung gefunden'
            )
        for area in areas:
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Anzahl Arbeitsplätze (Orientierungswerte)")
            diagram = ArbeitsplatzEntwicklung(area=area, title=title)
            diagram.draw()

            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Branchenanteile an den Arbeitsplätzen")
            diagram = BranchenAnteile(area=area, title=title)
            diagram.draw(offset_x=100, offset_y=100)
