from projektcheck.base import (Domain, Params, Param, SpinBox, ComboBox,
                               Title, Seperator, LineEdit, Geopackage, Field,
                               Slider, DoubleSpinBox, SumDependency)
from projektcheck.utils.utils import clearLayout
from projektcheck.domains.constants import Nutzungsart
from projektcheck.domains.definitions.tables import Areas


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projekt-Definitionen'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(self.change_area)

        self.building_types = self.basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        )
        self.assortments = self.basedata.get_table(
            'Einzelhandel_Sortimente', 'Definition_Projekt'
        )
        self.industries = self.basedata.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt'
        )

        self.areas = Areas.features()
        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        for area in self.areas:
            self.ui.area_combo.addItem(area.name, area.id)
        self.ui.area_combo.blockSignals(False)
        self.setup_type()
        self.setup_type_params()

    def change_area(self, index):
        self.setup_type()
        self.setup_type_params()

    def setup_type(self):

        area_id = self.ui.area_combo.itemData(self.ui.area_combo.currentIndex())
        self.area = self.areas.get(id=area_id)
        layout = self.ui.parameter_group.layout()
        clearLayout(layout)
        self.params = Params(layout)
        self.params.name = Param(self.area.name, LineEdit(), label='Name')
        self.params.area = Param(round(self.area.geom.area()), label='Größe')
        type_names = [n.capitalize() for n in Nutzungsart._member_names_]

        self.params.typ = Param(
            Nutzungsart(self.area.nutzungsart).name.capitalize(),
            ComboBox(type_names),
            label='Nutzungsart'
        )
        self.params.show()

        def type_changed():
            name = self.params.name.value
            self.area.nutzungsart = Nutzungsart[
                self.params.typ.value.upper()].value
            self.ui.area_combo.setItemText(
                self.ui.area_combo.currentIndex(), name)
            self.area.name = name
            self.area.save()
            self.setup_type_params()
            self.canvas.refreshAllLayers()
        self.params.changed.connect(type_changed)

    def setup_type_params(self):
        typ = self.params.typ.value
        if getattr(self, 'type_params', None):
            self.type_params.close()
            del self.type_params
        layout = self.ui.type_parameter_group.layout()
        # clear layout with parameters
        clearLayout(layout)
        self.type_params = Params(layout)
        if typ == 'Wohnen':
            self.setup_living_params()
        elif typ == 'Gewerbe':
            self.setup_industry_params()
        elif typ == 'Einzelhandel':
            self.setup_retail_params()
        else:
            return

        self.type_params.show()
        self.type_params.changed.connect(lambda: self.save_params(typ))

    def setup_living_params(self):
        #table = self.workspace.get_table('Wohnen_Struktur_und_Alterung_WE')

        self.type_params.add(Title('Bezugszeitraum'))
        #params.begin = Param(0, Slider(minimum=2000, maximum=2100),
                                  #label='Beginn des Bezuges')
        self.type_params.begin = Param(
            2000, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges'
        )
        self.type_params.period = Param(1, SpinBox(minimum=1, maximum=100),
                                        label='Dauer des Bezuges')
        self.type_params.add(Seperator())

        self.type_params.add(Title('Anzahl Wohneinheiten nach Gebäudetypen'))

        for bt in self.building_types.features():
            param_name = bt.param_we
            self.type_params.add(Param(
                getattr(self.area, param_name), Slider(maximum=500),
                label=f'... in {bt.display_name}'),
                name=param_name
            )
        self.type_params.add(Seperator())

        self.type_params.add(Title('Mittlere Anzahl Einwohner pro Wohneinheit\n'
                                   '(3 Jahre nach Bezug)'))

        for bt in self.building_types.features():
            param_name = bt.param_ew_je_we
            self.type_params.add(Param(
                getattr(self.area, param_name),
                DoubleSpinBox(step=0.1, maximum=50),
                label=f'... in {bt.display_name}'),
                name=param_name
            )

    def save_params(self, typ):
        if typ == 'Wohnen':
            for bt in self.building_types.features():
                for param_name in [bt.param_we, bt.param_ew_je_we]:
                    value = getattr(self.type_params, param_name).value
                    setattr(self.area, param_name, value)
        elif typ == 'Gewerbe':
            for branche in self.industries.features():
                param_name = branche.param_gewerbenutzung
                value = getattr(self.type_params, param_name).value
                setattr(self.area, param_name, value)
        elif typ == 'Einzelhandel':
            for assortment in self.assortments.features():
                param_name = assortment.param_vfl
                value = getattr(self.type_params, param_name).value
                setattr(self.area, param_name, value)
        self.area.save()
        self.canvas.refreshAllLayers()

        #if we_changed:
            #we_idx = self.df_acc_units['IDTeilflaeche'] == area['id_teilflaeche']
            #sums = self.df_acc_units[we_idx]['WE'].sum()
            #self.df_areas.loc[area_idx, 'WE_gesamt'] = sums
            #self.update_pretty_name()

    def setup_industry_params(self):

        self.type_params.add(Title('Bezugszeitraum'))
        self.type_params.begin = Param(
            2000, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges'
        )
        self.type_params.period = Param(
            1, SpinBox(minimum=1, maximum=100),
            label='Dauer des Bezuges (Jahre, 1 = Bezug wird noch\n'
            'im Jahr des Bezugsbeginns abgeschlossen)')
        self.type_params.add(Seperator())

        self.type_params.add(
            Title('Voraussichtlicher Anteil der Branchen an der Nettofläche'))

        dependency = SumDependency(100)
        for branche in self.industries.features():
            param = Param(
                getattr(self.area, branche.param_gewerbenutzung),
                Slider(maximum=100, width=200),
                # great column naming by the way ^^
                label=f'{branche.Name_Branche_ProjektCheck}', unit='%'
            )
            dependency.add(param)
            self.type_params.add(param, name=branche.param_gewerbenutzung)

        self.type_params.add(Seperator())

        self.type_params.add(Title('Voraussichtliche Anzahl an Arbeitsplätzen'))

        self.type_params.arbeitsplaetze_insgesamt = Param(
            0, Slider(maximum=10000),
            label='Schätzung der Zahl der Arbeitsplätze\n'
            'nach Vollbezug (Summe über alle Branchen)'
        )

    def setup_retail_params(self):
        self.type_params.add(Title('Verkaufsfläche'))

        for assortment in self.assortments.features():
            self.type_params.add(Param(
                getattr(self.area, assortment.param_vfl),
                Slider(maximum=20000),
                label=f'{assortment.Name_Sortiment_ProjektCheck}', unit='m²'),
                name=assortment.param_vfl
            )

    def close(self):
        # ToDo: implement this in project (collecting all used workscpaces)
        if hasattr(self, 'areas'):
            self.areas._table.workspace.close()
        super().close()
