from pctools.base import (Domain, Params, Param, SpinBox, ComboBox,
                          Title, Seperator, LineEdit, Geopackage,
                          Slider)
from pctools.definitions.basetable_definitions import BuildingTypes

def clearLayout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.layout() is not None:
            clearLayout(child.layout())


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projekt-Definitionen'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'
    workspace = 'Definition_Projekt'

    def setupUi(self):
        for area in self.project.areas:
            self.ui.area_combo.addItem(area)
        self.ui.area_combo.currentTextChanged.connect(self.change_area)

        self.building_types = BuildingTypes(self.basedata)

        # ToDo: take from database
        #for typ in ['Wohnen', 'Gewerbe', 'Einzelhandel']:
            #self.ui.type_combo.addItem(typ)
        #self.ui.type_combo.currentTextChanged.connect(self.setup_type)
        self.setup_type()
        self.setup_type_params()

    def change_area(self, area):
        pass

    def setup_type(self):
        layout = self.ui.parameter_group.layout()
        self.params = Params(layout)
        self.params.name = Param('fläche1', LineEdit(), label='Name')
        self.params.area = Param(0, label='Größe')
        self.params.typ = Param(
            'Wohnen', ComboBox(['Wohnen', 'Gewerbe', 'Einzelhandel']),
            label='Nutzungsart'
        )
        self.params.show()
        self.params.changed.connect(self.setup_type_params)

    def setup_type_params(self):
        typ = self.params.typ.value
        if getattr(self, 'type_params', None):
            self.type_params.close()
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

        self.type_params.show()
        self.type_params.changed.connect(lambda: print('params changed'))

    def setup_living_params(self):
        table = self.projectdata.get_table(
            'Wohnen_Struktur_und_Alterung_WE', self.workspace)

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

        for bt in self.building_types.values():
            # ToDo: slider
            self.type_params.add(Param(
                0, Slider(maximum=500),
                label=f'Anzahl WE in {bt.display_name}'),
                name=bt.param_we
            )
        self.type_params.add(Seperator())

        self.type_params.add(Title('Mittlere Anzahl Einwohner pro Wohneinheit\n'
                                   '(3 Jahre nach Bezug)'))

        for bt in self.building_types.values():
            self.type_params.add(Param(
                0, Slider(maximum=500), label=f'... in {bt.display_name}'),
                name=bt.param_ew_je_we
            )

    def save_living(self):
        pass

    def setup_industry_params(self):
        #table = self.projectdata.get_table('irgendwas', self.workspace)
        pass

    def setup_retail_params(self):
        #table = self.projectdata.get_table('irgendwas', self.workspace)
        pass

    def close(self):
        #if getattr(self, 'type_params', None):
            #self.type_params.close()
        #if getattr(self, 'params', None):
            #self.params.close()
        super().close()
