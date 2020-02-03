from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.base.diagrams import BarChart, PieChart
from projektcheck.domains.landuse.tables import (WohnbaulandAnteile,
                                                 WohnflaecheGebaeudetyp,
                                                 GrenzeSiedlungskoerper)
from projektcheck.domains.definitions.tables import (Wohneinheiten,
                                                     Projektrahmendaten)
from projektcheck.domains.constants import Nutzungsart
from projektcheck.base.params import Params, Param, Title, Seperator
from projektcheck.base.layers import TileLayer
from projektcheck.base.inputs import Slider
from projektcheck.utils.utils import clearLayout
from projektcheck.base.tools import LineMapTool

from settings import settings


class LandUse(Domain):
    """"""

    ui_label = 'Flächeninanspruchnahme'
    ui_file = 'ProjektCheck_dockwidget_analysis_05-Fl.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_landuse_1.png"
    layer_group = 'Wirkungsbereich 5 - Flächeninanspruchnahme'

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(
            lambda: self.change_area())
        self.layout = self.ui.parameter_group.layout()
        self.ui.calculate_density_button.clicked.connect(
            self.calculate_wohndichte)
        self.ui.calculate_areadensity_button.clicked.connect(
            self.calculate_wohnflaechendichte)
        self.ui.power_lines_button.clicked.connect(self.add_power_lines)
        self.ui.power_lines_button.setCheckable(False)
        self.ui.calculate_integration_button.clicked.connect(
            self.calculate_integration)
        self.bordertool = LineMapTool(
            self.ui.draw_border_button, canvas=self.canvas,
            line_width=3)# , color='#33ccff')
        self.bordertool.drawn.connect(self.add_border)

        self.ui.remove_drawing_button.clicked.connect(self.remove_borders)

    def load_content(self):
        self.gebaeudetypen_base = self.basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        )
        self.areas = Teilflaechen.features()
        self.living_areas = Teilflaechen.features().filter(
            nutzungsart=Nutzungsart.WOHNEN.value)
        self.wohnbauland_anteile = WohnbaulandAnteile.features(create=True)
        self.wohnflaeche = WohnflaecheGebaeudetyp.features(create=True)
        self.borders = GrenzeSiedlungskoerper.features(create=True)
        self.wohneinheiten = Wohneinheiten.features(create=True)
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
        for area in self.living_areas:
            self.ui.area_combo.addItem(area.name, area)
        self.ui.area_combo.blockSignals(False)

        self.add_border_output()

        self.change_area()

        self.area_union = None
        for area in self.areas:
            self.area_union = area.geom if not self.area_union \
                else self.area_union.combine(area.geom)
        self.bordertool.set_snap_geometry(self.area_union)

    def setup_params(self):
        anteile = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        value = anteile.nettoflaeche if anteile else 15
        clearLayout(self.layout)
        self.params = Params(
            self.layout,
            help_file='flaecheninanspruchnahme_wohnbauland_wohnflaeche.txt')
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

    def calculate_wohndichte(self):
        if not self.area:
            return
        # calculation for area
        anteile = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        netto_wb = (self.area.geom.area() / 10000 *
                    (1 - anteile.nettoflaeche / 100))
        wohndichte = round(self.area.we_gesamt / netto_wb, 1)

        # get data to compare to
        kreis, kreisname, kreistyp, typname = self.get_kreis_data()
        wohndichte_kreis = kreis.Wohndichte_WE_pro_ha_Nettowohnbauland
        wohndichte_kreistyp = kreistyp.Wohndichte_WE_pro_ha_Nettowohnbauland

        # chart
        values = [wohndichte, wohndichte_kreis, wohndichte_kreistyp]
        labels = [f'Teilfläche {self.area.name}', f'Kreis {kreisname}', typname]
        colors = ['r', 'b', 'b']
        chart = BarChart(values, labels=labels,
                         title=f'Teilfläche {self.area.name}: '
                         'Wohneinheiten pro Hektar Nettowohnbauland',
                         colors=colors, y_label='Wohneinheiten pro Hektar')
        chart.draw()

    def calculate_wohnflaechendichte(self):
        if not self.area:
            return
        # calculation for area
        anteile = self.wohnbauland_anteile.get(id_teilflaeche=self.area.id)
        wohneinheiten = self.wohneinheiten.filter(id_teilflaeche=self.area.id)
        wohnflaeche = self.wohnflaeche.filter(id_teilflaeche=self.area.id)

        df_wohneinheiten = wohneinheiten.to_pandas()
        df_wohnflaeche = wohnflaeche.to_pandas()
        df_merged = df_wohneinheiten.merge(df_wohnflaeche, on='id_gebaeudetyp')
        wohnflaeche_gesamt = (df_merged['mean_wohnflaeche'] *
                              df_merged['we']).sum()
        netto_wb = (self.area.geom.area() / 10000 *
                    (1 - anteile.nettoflaeche / 100))
        wohnflaechendichte = round(wohnflaeche_gesamt / netto_wb, 1)

        # get data to compare to
        kreis, kreisname, kreistyp, typname = self.get_kreis_data()
        wohndichte_kreis = \
            kreis.Wohnflaechendichte_qm_Wohnfl_pro_ha_Nettowohnbauland
        wohndichte_kreistyp = \
            kreistyp.Wohnflaechendichte_qm_Wohnfl_pro_ha_Nettowohnbauland

        # chart
        values = [wohnflaechendichte, wohndichte_kreis, wohndichte_kreistyp]
        labels = [f'Teilfläche {self.area.name}', f'Kreis {kreisname}', typname]
        colors = ['r', 'b', 'b']
        chart = BarChart(values, labels=labels,
                         title=f'{self.project.name} - {self.area.name}: '
                         'Wohnfläche(m²) pro Hektar Nettowohnbauland',
                         colors=colors, y_label='Quadratmeter pro Hektar')
        chart.draw()

    def get_kreis_data(self):
        ags5 = str(self.rahmendaten.ags)[0:5]
        kreis = self.wohndichte_kreis.features().get(AGS5=ags5)
        kreistyp_id = kreis.Siedlungsstruktureller_Kreistyp
        kreistyp = self.wohndichte_raumtyp.features().get(
            Siedlungsstruktureller_Kreistyp=kreistyp_id)
        kreisname = kreis.Kreis_kreisfreie_Stadt.split(',')[0]
        typname = self.raumtypen.features().get(ID=kreistyp_id).Name
        return kreis, kreisname, kreistyp, typname

    def add_power_lines(self):
        group = (f'{self.project.groupname}/{self.layer_group}')
        geoserver = ('https://geoserver.ggr-planung.de/geoserver/'
                     'projektcheck/wms?')
        layername = '51005_ax_leitung'
        url = (f'url={geoserver}&layers={layername}&crs=EPSG:{settings.EPSG}'
               '&format=image/png&dpiMode=7&styles')
        layer = TileLayer(url, groupname=group)
        layer.draw('Hochspannungsleitungen')

    def add_border(self, geom):
        self.borders.add(geom=geom)
        # workaround: layer style is not applied correctly
        # with empty features -> redraw on first geometry
        if len(self.borders) == 1:
            self.add_border_output()
        self.canvas.refreshAllLayers()

    def remove_borders(self):
        self.borders.delete()
        self.canvas.refreshAllLayers()

    def add_border_output(self):
        self.output_border = ProjectLayer.from_table(
            self.borders.table, groupname=self.layer_group,
            prepend=True)
        self.output_border.draw(
            label='Grenze Siedlunskörper',
            style_file='flaeche_oekologie_grenze_siedlungskoerper.qml'
        )

    def calculate_integration(self):
        area_outer_border = self.area_union.length()
        drawn_borders = sum([line.geom.length() for line in self.borders])
        shared_border = round(drawn_borders / area_outer_border, 3) * 100
        shared_border = min(shared_border, 100)
        values = [shared_border, 100 - shared_border]
        labels = ['an bestehende Siedlungen angrenzend',
                  'nicht an bestehende Siedlungen angrenzend']
        chart = PieChart(values, labels=labels, colors=None,
                         title=f'{self.project.name}: Anteil der '
                         'Plangebietsgrenze',)
        chart.draw()


    def close(self):
        # ToDo: implement this in project (collecting all used workscpaces)
        output = ProjectLayer.find('Nutzungen des Plangebiets')
        if output:
            layer = output[0].layer()
            layer.removeSelection()
        if hasattr(self, 'areas'):
            self.living_areas.table.workspace.close()
        super().close()