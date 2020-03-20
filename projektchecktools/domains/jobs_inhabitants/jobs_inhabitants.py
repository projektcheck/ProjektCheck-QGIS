import os
from qgis.PyQt.QtWidgets import QMessageBox
from qgis import utils

from projektchecktools.base.domain import Domain
from projektchecktools.domains.constants import Nutzungsart
from projektchecktools.domains.jobs_inhabitants.diagrams import (
    BewohnerEntwicklung, ArbeitsplatzEntwicklung, BranchenAnteile)
from projektchecktools.domains.definitions.tables import Teilflaechen
from projektchecktools.utils.utils import open_file
from projektchecktools.base.project import ProjectLayer
from projektchecktools.domains.definitions.tables import Gewerbeanteile
from projektchecktools.domains.jobs_inhabitants.tables import (
    WohnenProJahr, ApProJahr)


class JobsInhabitants(Domain):
    """"""
    ui_label = 'Bewohner und Arbeitsplätze'
    ui_file = 'ProjektCheck_dockwidget_analysis_01-BA.ui'
    ui_icon = 'images/iconset_mob/20190619_iconset_mob_people_1.png'
    layer_group = 'Wirkungsbereich 1 - Bewohner und Arbeitsplätze'

    def setupUi(self):
        self.ui.inhabitants_button.clicked.connect(self.inhabitants_diagram)
        self.ui.jobs_button.clicked.connect(self.jobs_diagram)
        self.ui.inhabitants_table_button.clicked.connect(self.inhabitants_table)
        self.ui.jobs_table_button.clicked.connect(self.jobs_table)

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Bewohner_und_Arbeitsplätze.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

    def load_content(self):
        super().load_content()
        output = ProjectLayer.find('Projektdefinition')
        if output:
            output[0].setItemVisibilityChecked(True)

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
        for i, area in enumerate(areas):
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Einwohnerentwicklung")
            diagram = BewohnerEntwicklung(area=area, title=title)
            diagram.draw(offset_x=i*100, offset_y=i*100)

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
        for i, area in enumerate(areas):
            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Anzahl Arbeitsplätze (Orientierungswerte)")
            diagram = ArbeitsplatzEntwicklung(area=area, title=title)
            diagram.draw(offset_x=i*100, offset_y=i*100)

            title = (f"{self.project.name} - {area.name}: "
                     "Geschätzte Branchenanteile an den Arbeitsplätzen")
            diagram = BranchenAnteile(area=area, title=title)
            diagram.draw(offset_x=i*100+50, offset_y=i*100+50)

    def inhabitants_table(self):
        output = ProjectLayer.from_table(
            WohnenProJahr.get_table(), groupname=self.layer_group)
        layer = output.draw(label='Bewohnerschätzung nach Alter und Jahr')
        table_config = layer.attributeTableConfig()
        table_config.setSortExpression(
            '"id_teilflaeche" || "jahr" || "id_altersklasse"')
        layer.setAttributeTableConfig(table_config)
        utils.iface.showAttributeTable(layer)

    def jobs_table(self):
        output = ProjectLayer.from_table(
            ApProJahr.get_table(), groupname=self.layer_group)
        layer = output.draw(label='Arbeitsplätze insgesamt nach Jahr')
        table_config = layer.attributeTableConfig()
        table_config.setSortExpression('"id_teilflaeche" || "jahr"')
        layer.setAttributeTableConfig(table_config)
        utils.iface.showAttributeTable(layer)

        output = ProjectLayer.from_table(
            Gewerbeanteile.get_table(), groupname=self.layer_group)
        layer = output.draw(label='Branchenanteile')
        table_config = layer.attributeTableConfig()
        table_config.setSortExpression('"id_teilflaeche" || "id_branche"')
        layer.setAttributeTableConfig(table_config)
        utils.iface.showAttributeTable(layer)

    def close(self):
        output = ProjectLayer.find('Projektdefinition')
        if output:
            output[0].setItemVisibilityChecked(False)
        super().close()
