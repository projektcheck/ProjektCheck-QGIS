from qgis.PyQt.QtWidgets import QMessageBox

from projektchecktools.base.domain import Domain
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.domains.municipaltaxrevenue.tables import (
    Gemeinden, EinwohnerWanderung)
from projektchecktools.domains.municipaltaxrevenue.migration import (
    Migration)
from projektchecktools.domains.definitions.tables import (
    Projektrahmendaten, Teilflaechen)
from projektchecktools.utils.utils import clear_layout
from projektchecktools.base.params import Params, Param, Title
from projektchecktools.base.inputs import DoubleSpinBox


class MunicipalTaxRevenue(Domain):
    """"""

    ui_label = 'kommunale Steuereinnahmen'
    ui_file = 'ProjektCheck_dockwidget_analysis_07-KSt.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_tax_1.png"
    layer_group = 'Wirkungsbereich 7 - Kommunale Steuereinnahmen'
    radius = 25000

    def setupUi(self):
        self.ui.migration_inhabitants_button.clicked.connect(
            self.calculate_migration_einwohner)
        self.einwohner_params = None

    def load_content(self):
        super().load_content()
        self.gemeinden = Gemeinden.features(create=True)
        self.project_frame = Projektrahmendaten.features()[0]
        self.wanderung_ew = EinwohnerWanderung.features(create=True)
        if len(self.gemeinden) == 0:
            self.get_gemeinden()

        self.areas = Teilflaechen.features()

        self.setup_einwohner_params()

    def get_gemeinden(self):
        gemeinden = self.basedata.get_table('bkg_gemeinden',
                                            'Basisdaten_deutschland')
        buffer_geom = self.project_frame.geom.buffer(self.radius, 5)
        gemeinden.spatial_filter(buffer_geom.asWkt())
        # project table has some of the fields of the basedata table
        # (same names)
        common_fields = set([f.name for f in gemeinden.fields()]).intersection(
            [f.name for f in self.gemeinden.fields()])
        for gemeinde in gemeinden:
            attrs = {}
            for field in common_fields:
                attrs[field] = gemeinde[field]
            attrs['geom'] = gemeinde['geom']
            self.gemeinden.add(**attrs)

    def calculate_migration_einwohner(self):
        sum_ew = sum(self.areas.values('ew'))
        if sum_ew == 0:
            QMessageBox.warning(self.ui, 'Fehler',
                                'Es wurden keine definierten Teilflächen mit '
                                'der Nutzungsart "Wohnen" gefunden.')
            return

        job = Migration(self.project)

        def on_close():
            if not self.dialog.success:
                return
            self.setup_einwohner_params()

        self.dialog = ProgressDialog(job, parent=self.ui, on_close=on_close)
        self.dialog.show()

    def setup_einwohner_params(self):
        if self.einwohner_params:
            self.einwohner_params.close()
        layout = self.ui.einwohner_parameter_group.layout()
        clear_layout(layout)
        if len(self.wanderung_ew) == 0:
            self.ui.einwohner_parameter_group.setVisible(False)
            return
        self.ui.einwohner_parameter_group.setVisible(True)
        self.params = Params(
            layout, help_file='einnahmen_einwohner_wanderung.txt')

        project_ags = self.project_frame.ags

        project_gem = self.gemeinden.get(AGS=project_ags)
        wanderung = self.wanderung_ew.get(AGS=project_ags)

        self.params.add(Title('Standortgemeinde des Projekts'))

        self.params.project_saldo = Param(
            wanderung.saldo,
            DoubleSpinBox(minimum=0, maximum=1000, step=0.1, lockable=True,
                          locked=wanderung.fixed),
            label=f' -{project_gem.GEN}'
        )

        self.params.add(Title('Region um Standortgemeinde'))

        for gemeinde in self.gemeinden:
            if gemeinde.AGS == project_ags:
                continue
            wanderung = self.wanderung_ew.get(AGS=gemeinde.AGS)
            if not wanderung:
                continue
            param = Param(
                wanderung.saldo,
                DoubleSpinBox(minimum=0, maximum=1000, step=0.1, lockable=True,
                              locked=wanderung.fixed),
                label=f' -{gemeinde.GEN}'
            )
            self.params.add(param, name=gemeinde.AGS)

        def save():
            pass

        self.params.show(title='Geschätzte Salden (Einwohner) bearbeiten',
            scrollable=True)
        self.params.changed.connect(save)

        #we_gesamt = sum(self.areas.values('we_gesamt'))
        #decimals = 2 if we_gesamt < 1 else 0 if we_gesamt >= 20 else 1

    def close(self):
        if self.einwohner_params:
            self.einwohner_params.close()
        super().close()