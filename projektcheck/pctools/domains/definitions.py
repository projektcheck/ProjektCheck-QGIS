from pctools.base import (Domain, Params, Param, SpinBox,
                          Title, Seperator)
from pctools.backend import Geopackage


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
        for typ in ['Wohnen', 'Gewerbe', 'Einzelhandel']:
            self.ui.type_combo.addItem(typ)
        self.ui.type_combo.currentTextChanged.connect(self.change_type)
        self.params = None
        self.setup_living()

    def change_area(self, area):
        pass

    def change_type(self, typ):
        if self.params:
            self.params.close()

    def setup_living(self):
        table = self.projectdata.get_table(
            'Wohnen_Struktur_und_Alterung', self.workspace)
        self.params = Params(self.ui.param_layout)

        self.params.add(Title('Bezugszeitraum'))
        #self.params.begin = Param(0, Slider(minimum=2000, maximum=2100),
                                  #label='Beginn des Bezuges')
        self.params.begin = Param(0, SpinBox(),
                                  label='Beginn des Bezuges')
        self.params.period = Param(0, SpinBox(), label='Dauer des Bezuges')
        self.params.add(Seperator())

        self.params.add(Title('Mittlere Anzahl Einwohner pro Wohneinheit\n'
                              '(3 Jahre nach Bezug)'))
        self.params.eh = Param(0, SpinBox(), label='in Einfamilienhäusern')
        self.params.zh = Param(0, SpinBox(), label='in Zweifamilienhäusern')
        self.params.rh = Param(0, SpinBox(), label='in Reihenhäusern')
        self.params.mfh = Param(0, SpinBox(), label='in Mehrfamilienhäusern')
        self.params.add(Seperator())

        self.params.add(Title('Anzahl Wohneinheiten nach Gebäudetypen'))
        self.params.eh_we = Param(0, SpinBox(),
                                  label='Anzahl WE in Einfamilienhäusern')
        self.params.zh_we = Param(0, SpinBox(),
                                  label='Anzahl WE in Zweifamilienhäusern')
        self.params.rh_we = Param(0, SpinBox(),
                                  label='Anzahl WE in Reihenhäusern')
        self.params.mfh_we = Param(0, SpinBox(),
                                   label='Anzahl WE in Mehrfamilienhäusern')

        self.params.show()

        self.params.changed.connect(lambda: print('params changed'))

    def save_living(self):
        pass

    def setup_industry(self):
        pass

    def setup_retail(self):
        pass

    def close(self):
        self.params.close()
        super().close()
