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
from projektchecktools.base.params import Params, Param, Title, Seperator
from projektchecktools.base.inputs import DoubleSpinBox, SpinBox


class Grundsteuer:
    def __init__(self, project, ui):
        self.project = project
        self.ui = ui
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.gemeinden = Gemeinden.features()
        self.hebesatz_params = None

    def load_content(self):
        self.gemeinden = Gemeinden.features(create=True)
        self.setup_hebesatz()

    def setup_hebesatz(self):
        if self.hebesatz_params:
            self.hebesatz_params.close()
        layout = self.ui.grundsteuer_hebesatz_param_group.layout()
        clear_layout(layout)
        self.params = Params(
            layout, help_file='einnahmen_grundsteuer_hebesatz.txt')

        project_gem = self.gemeinden.get(AGS=self.project_frame.ags)

        self.params.hebesatz = Param(
            project_gem.Hebesatz_GrStB,
            SpinBox(maximum=10000, step=10),
            label='Hebesatz GrSt B Projektgemeinde',
            unit='v.H.'
        )

        def save():
            project_gem.Hebesatz_GrStB = self.params.hebesatz.value
            project_gem.save()

        self.params.show(title='Hebesatz bearbeiten')
        self.params.changed.connect(save)

    def close(self):
        if self.hebesatz_params:
            self.hebesatz_params.close()


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
        self.grundsteuer = Grundsteuer(self.project, self.ui)

    def load_content(self):
        super().load_content()
        self.gemeinden = Gemeinden.features(create=True)
        self.project_frame = Projektrahmendaten.features()[0]
        self.wanderung_ew = EinwohnerWanderung.features(create=True)
        if len(self.gemeinden) == 0:
            self.get_gemeinden()
        self.areas = Teilflaechen.features()

        self.grundsteuer.load_content()

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

        self.df_wanderung = self.wanderung_ew.to_pandas()

        def update_salden(ags_changed):
            param = self.params[ags_changed]
            fixed = not param.is_locked
            saldo = param.input.value
            idx = self.df_wanderung['AGS'] == ags_changed
            self.df_wanderung.loc[idx, 'fixed'] = fixed
            self.df_wanderung.loc[idx, 'saldo'] = saldo
            if fixed:
                zuzug = self.df_wanderung[idx]['zuzug'].values[0]
                self.df_wanderung.loc[idx, 'fortzug'] = zuzug - saldo
            self.df_wanderung = Migration.calculate_saldi(
                self.df_wanderung, factor, project_ags)
            for gemeinde_ags in self.df_wanderung['AGS'].values:
                param = self.params[gemeinde_ags]
                row = self.df_wanderung[self.df_wanderung['AGS']==gemeinde_ags]
                param.input.blockSignals(True)
                param.input.value = row['saldo'].values[0]
                param.input.blockSignals(False)

        project_ags = self.project_frame.ags

        project_gem = self.gemeinden.get(AGS=project_ags)
        wanderung = self.wanderung_ew.get(AGS=project_ags)

        self.params.add(Title('Standortgemeinde des Projekts'))

        spinbox = DoubleSpinBox(minimum=-1000, maximum=1000, step=1,
                                lockable=True, locked=not wanderung.fixed)
        project_saldo = Param(wanderung.saldo, spinbox,
                              label=f' -{project_gem.GEN}')
        self.params.add(project_saldo, name=project_ags)
        spinbox.changed.connect(lambda o: update_salden(project_ags))
        spinbox.locked.connect(lambda o: update_salden(project_ags))

        self.params.add(Seperator())
        self.params.add(Title('Region um Standortgemeinde'))

        randsummen = self.project.basedata.get_table(
            'Wanderung_Randsummen', 'Einnahmen').features()
        factor = randsummen.get(IDWanderungstyp=1).Anteil_Wohnen
        sum_ew = sum(self.areas.values('ew'))

        for gemeinde in self.gemeinden:
            ags = gemeinde.AGS
            if ags == project_ags:
                continue
            wanderung = self.wanderung_ew.get(AGS=ags)
            if not wanderung:
                continue
            spinbox = DoubleSpinBox(minimum=-1000, maximum=1000, step=1,
                                    lockable=True, locked=not wanderung.fixed)
            param = Param(wanderung.saldo, spinbox, label=f' -{gemeinde.GEN}')
            self.params.add(param, name=ags)
            spinbox.changed.connect(lambda o, a=ags: update_salden(a))
            spinbox.locked.connect(lambda o, a=ags: update_salden(a))

        self.params.add(Seperator())

        self.params.add(Param(
            (factor - 1) * sum_ew,
            label='Restliches Bundesgebiet / Ausland'
        ))

        def save():
            self.wanderung_ew.update_pandas(self.df_wanderung)

        self.params.show(title='Geschätzte Salden (Einwohner) bearbeiten',
            scrollable=True)
        self.params.changed.connect(save)

        #we_gesamt = sum(self.areas.values('we_gesamt'))
        #decimals = 2 if we_gesamt < 1 else 0 if we_gesamt >= 20 else 1

    def close(self):
        if self.einwohner_params:
            self.einwohner_params.close()
        self.grundsteuer.close()
        super().close()