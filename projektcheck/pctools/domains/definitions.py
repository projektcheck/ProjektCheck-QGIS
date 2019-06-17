from pctools.base import (Domain, Params, Param, SpinBox, ComboBox,
                          Title, Seperator, LineEdit)
from pctools.backend import Geopackage

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
            self.add_living_params()
        elif typ == 'Gewerbe':
            self.add_industry_params()
        elif typ == 'Einzelhandel':
            self.add_retail_params()

        self.type_params.show()
        self.type_params.changed.connect(lambda: print('params changed'))

    def add_living_params(self):
        table = self.projectdata.get_table(
            'Wohnen_Struktur_und_Alterung', self.workspace)

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

        self.type_params.add(Title('Mittlere Anzahl Einwohner pro Wohneinheit\n'
                                   '(3 Jahre nach Bezug)'))
        self.type_params.eh = Param(
            0, SpinBox(), label='in Einfamilienhäusern')
        self.type_params.zh = Param(
            0, SpinBox(), label='in Zweifamilienhäusern')
        self.type_params.rh = Param(
            0, SpinBox(), label='in Reihenhäusern')
        self.type_params.mfh = Param(
            0, SpinBox(), label='in Mehrfamilienhäusern')
        self.type_params.add(Seperator())

        self.type_params.add(Title('Anzahl Wohneinheiten nach Gebäudetypen'))
        self.type_params.eh_we = Param(
            0, SpinBox(), label='Anzahl WE in Einfamilienhäusern')
        self.type_params.zh_we = Param(
            0, SpinBox(), label='Anzahl WE in Zweifamilienhäusern')
        self.type_params.rh_we = Param(
            0, SpinBox(), label='Anzahl WE in Reihenhäusern')
        self.type_params.mfh_we = Param(
            0, SpinBox(), label='Anzahl WE in Mehrfamilienhäusern')

    def save_living(self):
        pass

    def add_industry_params(self):
        table = self.projectdata.get_table('irgendwas', self.workspace)

    def add_retail_params(self):
        table = self.projectdata.get_table('irgendwas', self.workspace)

    def close(self):
        #if getattr(self, 'type_params', None):
            #self.type_params.close()
        #if getattr(self, 'params', None):
            #self.params.close()
        super().close()
