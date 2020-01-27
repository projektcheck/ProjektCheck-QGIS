from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.base.diagrams import BarChart
from projektcheck.domains.landuse.tables import (WohnbaulandAnteile,
                                                 WohnflaecheGebaeudetyp)
from projektcheck.domains.definitions.tables import (Wohneinheiten,
                                                     Projektrahmendaten)
from projektcheck.domains.constants import Nutzungsart
from projektcheck.base.params import Params, Param, Title, Seperator
from projektcheck.base.inputs import Slider
from projektcheck.utils.utils import clearLayout


class LandUse(Domain):
    """"""

    ui_label = 'Flächeninanspruchnahme'
    ui_file = 'ProjektCheck_dockwidget_analysis_05-Fl.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_landuse_1.png"

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(
            lambda: self.change_area())
        self.layout = self.ui.parameter_group.layout()
        self.ui.calculate_density_button.clicked.connect(self.calculate_density)

    def load_content(self):
        self.gebaeudetypen_base = self.basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        )
        self.areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.WOHNEN.value)
        self.wohnbauland_anteile = WohnbaulandAnteile.features(create=True)
        self.wohnflaeche = WohnflaecheGebaeudetyp.features(create=True)
        self.wohneinheiten = Wohneinheiten.features()
        self.rahmendaten = Projektrahmendaten.features()[0]
        self.wohndichte_kreis = self.basedata.get_table(
            'Wohndichte_Wohnflaechendichte_Kreise', 'Flaeche_und_Oekologie')
        self.wohndichte_raumtyp = self.basedata.get_table(
            'Wohndichte_Wohnflaechendichte_RaumTypen',
            'Flaeche_und_Oekologie')
        self.raumtypen = self.basedata.get_table(
            'RaumTypen', 'Flaeche_und_Oekologie')

        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        for area in self.areas:
            self.ui.area_combo.addItem(area.name, area)
        self.ui.area_combo.blockSignals(False)

        self.change_area()

    def setup_params(self):
        anteile = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        value = anteile.nettoflaeche if anteile else 15
        clearLayout(self.layout)
        self.params = Params(self.layout,
                             help_file='flaechennutzung_params.txt')
        self.params.add(Title('Wohnbauland'))
        self.params.nettoflaeche = Param(
            value, Slider(maximum=100),
            label='Anteil der Fläche der ausgewählten Teilfläche,\n'
            'welcher kein Nettowohnbauland\n'
            '(= Wohnbaugrundstücke) ist',
            unit='%'
        )

        self.params.add(Seperator())

        self.params.add(Title('Durchschnittliche Wohnfläche je Wohneinheit'))

        for bt in self.gebaeudetypen_base.features():
            param_name = bt.param_we
            feature = self.wohnflaeche.get(id_gebaeudetyp=bt.id,
                                           id_teilflaeche=self.area.id)
            # default value on first time
            value = bt.Wohnfl_m2_pro_WE if not feature \
                else feature.mean_wohnflaeche
            self.params.add(Param(
                value, Slider(maximum=200),
                label=f'... in {bt.display_name}'),
                name=param_name
            )

        self.params.changed.connect(self.save)
        self.params.show()

        # ToDo: check features if they have to be created instead of saving on
        # suspicion
        self.save()

    def save(self):

        feature = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        # ToDo: get_or_create
        if not feature:
            feature = self.wohnbauland_anteile.add(id_teilflaeche=self.area.id)
        feature.nettoflaeche = self.params.nettoflaeche.value
        feature.save()

        for bt in self.gebaeudetypen_base.features():
            feature = self.wohnflaeche.get(id_gebaeudetyp=bt.id,
                                           id_teilflaeche=self.area.id)
            if not feature:
                feature = self.wohnflaeche.add(
                    id_gebaeudetyp=bt.id, id_teilflaeche=self.area.id)
            feature.mean_wohnflaeche = getattr(
                self.params, bt.param_we).value
            feature.save()

    def change_area(self):

        self.area = self.ui.area_combo.itemData(
            self.ui.area_combo.currentIndex())
        if not self.area:
            return

        output = ProjectLayer.find('Nutzungen des Plangebiets')
        if output:
            layer = output[0].layer()
            layer.removeSelection()
            layer.select(self.area.id)

        self.setup_params()

    def calculate_density(self):
        anteile = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        netto_wb = (self.area.geom.area() / 10000 *
                    (1 - anteile.nettoflaeche / 100))
        wohndichte = round(self.area.we_gesamt / netto_wb, 1)
        ags5 = str(self.rahmendaten.ags)[0:5]
        kreis = self.wohndichte_kreis.features().get(AGS5=ags5)
        wohndichte_kreis = kreis.Wohndichte_WE_pro_ha_Nettowohnbauland
        kreistyp_id = kreis.Siedlungsstruktureller_Kreistyp
        kreistyp = self.wohndichte_raumtyp.features().get(
            Siedlungsstruktureller_Kreistyp=kreistyp_id)
        wohndichte_kreistyp = kreistyp.Wohndichte_WE_pro_ha_Nettowohnbauland
        kreisname = kreis.Kreis_kreisfreie_Stadt.split(',')[0]
        typname = self.raumtypen.features().get(ID=kreistyp_id).Name
        values = [wohndichte, wohndichte_kreis, wohndichte_kreistyp]
        labels = [f'Teilfläche {self.area.name}', f'Kreis {kreisname}', typname]
        colors = ['r', 'b', 'b']
        chart = BarChart(values, labels=labels,
                         title='Wohneinheiten pro Hektar Nettowohnbauland',
                         colors=colors)
        chart.draw()

    def close(self):
        # ToDo: implement this in project (collecting all used workscpaces)
        output = ProjectLayer.find('Nutzungen des Plangebiets')
        if output:
            layer = output[0].layer()
            layer.removeSelection()
        if hasattr(self, 'areas'):
            self.areas._table.workspace.close()
        super().close()