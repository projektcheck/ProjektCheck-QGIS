from qgis.PyQt.QtWidgets import QMessageBox
import numpy as np

from projektchecktools.base.domain import Domain
from projektchecktools.base.dialogs import ProgressDialog
from projektchecktools.domains.municipaltaxrevenue.tables import (
    Gemeinden, EinwohnerWanderung, BeschaeftigtenWanderung, GrundsteuerSettings)
from projektchecktools.domains.municipaltaxrevenue.migration import (
    EwMigrationCalculation, SvBMigrationCalculation, MigrationCalculation)
from projektchecktools.domains.definitions.tables import (
    Projektrahmendaten, Teilflaechen)
from projektchecktools.utils.utils import clear_layout
from projektchecktools.base.params import Params, Param, Title, Seperator
from projektchecktools.base.inputs import DoubleSpinBox, SpinBox


class Migration:
    radius = 25000

    def __init__(self, project, ui):
        self.project = project
        self.ui = ui
        self.params = None

    def load_content(self):
        self.project_frame = Projektrahmendaten.features(
            project=self.project)[0]
        self.grst_settings = GrundsteuerSettings.features(create=True)
        self.gemeinden = Gemeinden.features(create=True)
        self.project_frame = Projektrahmendaten.features()[0]
        self.wanderung = EinwohnerWanderung.features(create=True)
        if len(self.gemeinden) == 0:
            self.get_gemeinden()
        self.areas = Teilflaechen.features()

    def get_gemeinden(self):
        gemeinden = self.project.basedata.get_table('bkg_gemeinden',
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

    def close(self):
        if self.params:
            self.params.close()


class EinwohnerMigration(Migration):

    def __init__(self, project, ui):
        super().__init__(project, ui)
        self.ui.migration_inhabitants_button.clicked.connect(self.calculate)

    def load_content(self):
        super().load_content()
        self.wanderung = EinwohnerWanderung.features(create=True)
        self.setup_params()

    def calculate(self):
        # ToDo: remove results depending on this
        sum_ew = sum(self.areas.values('ew'))
        if sum_ew == 0:
            QMessageBox.warning(self.ui, 'Fehler',
                                'Es wurden keine definierten Teilflächen mit '
                                'der Nutzungsart "Wohnen" gefunden.')
            return

        job = EwMigrationCalculation(self.project)

        def on_close():
            if not self.dialog.success:
                # ToDo: remove results
                return
            self.setup_params()

        self.dialog = ProgressDialog(job, parent=self.ui, on_close=on_close)
        self.dialog.show()

    def setup_params(self):
        if self.params:
            self.params.close()
        layout = self.ui.einwohner_parameter_group.layout()
        clear_layout(layout)
        if len(self.wanderung) == 0:
            self.ui.einwohner_parameter_group.setVisible(False)
            return
        self.ui.einwohner_parameter_group.setVisible(True)
        self.params = Params(
            layout, help_file='einnahmen_einwohner_wanderung.txt')

        self.df_wanderung = self.wanderung.to_pandas()

        randsummen = self.project.basedata.get_table(
            'Wanderung_Randsummen', 'Einnahmen').features()
        factor_inner = randsummen.get(IDWanderungstyp=1).Anteil_Wohnen
        factor_outer = randsummen.get(IDWanderungstyp=2).Anteil_Wohnen
        project_ags = self.project_frame.ags
        project_gem = self.gemeinden.get(AGS=project_ags)
        wanderung = self.wanderung.get(AGS=project_ags)
        sum_ew = sum(self.areas.values('ew'))

        def update_salden(ags_changed):
            param = self.params[ags_changed]
            fixed = param.is_locked
            saldo = param.input.value
            idx = self.df_wanderung['AGS'] == ags_changed
            if fixed:
                fixed_fortzug = self.df_wanderung[
                    np.invert(idx) & self.df_wanderung['fixed']==True
                    ]['fortzug'].sum()
                # the rest of "fortzüge" that can be applied to this row
                min_value = fixed_fortzug - (sum_ew * factor_inner)
                saldo = max(saldo, min_value)
                zuzug = self.df_wanderung[idx]['zuzug'].values[0]
                self.df_wanderung.loc[idx, 'fortzug'] = zuzug - saldo
            self.df_wanderung.loc[idx, 'fixed'] = fixed
            self.df_wanderung.loc[idx, 'saldo'] = saldo
            self.df_wanderung = MigrationCalculation.calculate_saldi(
                self.df_wanderung, factor_inner, project_ags)
            for gemeinde_ags in self.df_wanderung['AGS'].values:
                param = self.params[gemeinde_ags]
                row = self.df_wanderung[self.df_wanderung['AGS']==gemeinde_ags]
                param.input.blockSignals(True)
                param.input.value = row['saldo'].values[0]
                param.input.blockSignals(False)

        self.params.add(Title('Standortgemeinde des Projekts', bold=False))

        spinbox = DoubleSpinBox(minimum=0, maximum=1000, step=1,
                                lockable=True, locked=wanderung.fixed,
                                reversed_lock=True)
        project_saldo = Param(wanderung.saldo, spinbox,
                              label=f' -{project_gem.GEN}', unit='Einwohner')
        self.params.add(project_saldo, name=project_ags)
        spinbox.changed.connect(lambda o: update_salden(project_ags))
        spinbox.locked.connect(lambda o: update_salden(project_ags))

        self.params.add(Seperator())
        self.params.add(Title('Region um Standortgemeinde', bold=False))

        for gemeinde in sorted(self.gemeinden, key=lambda x: x.GEN):
            ags = gemeinde.AGS
            if ags == project_ags:
                continue
            wanderung = self.wanderung.get(AGS=ags)
            if not wanderung:
                continue
            spinbox = DoubleSpinBox(minimum=-1000, maximum=0, step=1,
                                    lockable=True, locked=wanderung.fixed,
                                    reversed_lock=True)
            param = Param(wanderung.saldo, spinbox, label=f' -{gemeinde.GEN}',
                          unit='Einwohner')
            self.params.add(param, name=ags)
            spinbox.changed.connect(lambda o, a=ags: update_salden(a))
            spinbox.locked.connect(lambda o, a=ags: update_salden(a))

        self.params.add(Seperator())

        self.params.add(Param(
            -factor_outer * sum_ew,
            label='Restliches Bundesgebiet / Ausland'
        ))

        def save():
            # ToDo: remove results depending on this
            self.wanderung.update_pandas(self.df_wanderung)

        self.params.show(title='Geschätzte Salden (Einwohner) bearbeiten',
            scrollable=True)
        self.params.changed.connect(save)


class BeschaeftigtenMigration(Migration):

    def __init__(self, project, ui):
        super().__init__(project, ui)
        self.ui.migration_jobs_button.clicked.connect(self.calculate)

    def load_content(self):
        super().load_content()
        self.wanderung = BeschaeftigtenWanderung.features(create=True)
        self.setup_params()

    def calculate(self):
        # ToDo: remove results depending on this
        sum_ap = sum(self.areas.values('ap_gesamt'))
        if sum_ap == 0:
            # ToDo: actually there are just no jobs
            # (e.g. when manually set to zero)
            QMessageBox.warning(self.ui, 'Fehler',
                                'Es wurden keine definierten Teilflächen mit '
                                'der Nutzungsart "Gewerbe" gefunden.')
            return

        job = SvBMigrationCalculation(self.project)

        def on_close():
            if not self.dialog.success:
                # ToDo: remove results of this calculation
                return
            self.setup_params()

        self.dialog = ProgressDialog(job, parent=self.ui, on_close=on_close)
        self.dialog.show()

    def setup_params(self):
        if self.params:
            self.params.close()
        layout = self.ui.svb_parameter_group.layout()
        clear_layout(layout)
        if len(self.wanderung) == 0:
            self.ui.svb_parameter_group.setVisible(False)
            return
        self.ui.svb_parameter_group.setVisible(True)
        self.params = Params(
            layout, help_file='einnahmen_beschaeftigte_wanderung.txt')

        self.df_wanderung = self.wanderung.to_pandas()

        randsummen = self.project.basedata.get_table(
            'Wanderung_Randsummen', 'Einnahmen').features()
        factor_inner = randsummen.get(IDWanderungstyp=1).Anteil_Gewerbe
        factor_outer = randsummen.get(IDWanderungstyp=2).Anteil_Gewerbe
        factor_neu = randsummen.get(IDWanderungstyp=3).Anteil_Gewerbe
        project_ags = self.project_frame.ags
        project_gem = self.gemeinden.get(AGS=project_ags)
        wanderung = self.wanderung.get(AGS=project_ags)
        sum_ap = sum(self.areas.values('ew'))

        # ToDo: this is exactly the same as in EinwohnerMigration
        def update_salden(ags_changed):
            param = self.params[ags_changed]
            fixed = param.is_locked
            saldo = param.input.value
            idx = self.df_wanderung['AGS'] == ags_changed
            if fixed:
                fixed_fortzug = self.df_wanderung[
                    np.invert(idx) & self.df_wanderung['fixed']==True
                    ]['fortzug'].sum()
                # the rest of "fortzüge" that can be applied to this row
                min_value = fixed_fortzug - (sum_ap * factor_inner)
                saldo = max(saldo, min_value)
                zuzug = self.df_wanderung[idx]['zuzug'].values[0]
                self.df_wanderung.loc[idx, 'fortzug'] = zuzug - saldo
            self.df_wanderung.loc[idx, 'fixed'] = fixed
            self.df_wanderung.loc[idx, 'saldo'] = saldo
            self.df_wanderung = MigrationCalculation.calculate_saldi(
                self.df_wanderung, factor_inner, project_ags)
            for gemeinde_ags in self.df_wanderung['AGS'].values:
                param = self.params[gemeinde_ags]
                row = self.df_wanderung[self.df_wanderung['AGS']==gemeinde_ags]
                param.input.blockSignals(True)
                param.input.value = row['saldo'].values[0]
                param.input.blockSignals(False)

        self.params.add(Title('Standortgemeinde des Projekts', bold=False))

        spinbox = DoubleSpinBox(minimum=0, maximum=1000, step=1,
                                lockable=True, locked=wanderung.fixed,
                                reversed_lock=True)
        project_saldo = Param(wanderung.saldo, spinbox,
                              label=f' -{project_gem.GEN}', unit='SvB')
        self.params.add(project_saldo, name=project_ags)
        spinbox.changed.connect(lambda o: update_salden(project_ags))
        spinbox.locked.connect(lambda o: update_salden(project_ags))

        self.params.add(Param(
            factor_neu * sum_ap,
            label='davon neu geschaffene Arbeitsplätze'
        ))

        self.params.add(Seperator())
        self.params.add(Title('Region um Standortgemeinde', bold=False))

        for gemeinde in sorted(self.gemeinden, key=lambda x: x.GEN):
            ags = gemeinde.AGS
            if ags == project_ags:
                continue
            wanderung = self.wanderung.get(AGS=ags)
            if not wanderung:
                continue
            spinbox = DoubleSpinBox(minimum=-1000, maximum=0, step=1,
                                    lockable=True, locked=wanderung.fixed,
                                    reversed_lock=True)
            param = Param(wanderung.saldo, spinbox, label=f' -{gemeinde.GEN}',
                          unit='SvB')
            self.params.add(param, name=ags)
            spinbox.changed.connect(lambda o, a=ags: update_salden(a))
            spinbox.locked.connect(lambda o, a=ags: update_salden(a))

        self.params.add(Seperator())

        self.params.add(Param(
            -factor_outer * sum_ap,
            label='Restliches Bundesgebiet / Ausland'
        ))

        def save():
            # ToDo: remove results depending on this
            self.wanderung.update_pandas(self.df_wanderung)

        self.params.show(title='Geschätzte Salden (Beschäftigte) bearbeiten',
                         scrollable=True)
        self.params.changed.connect(save)


class Grundsteuer:
    def __init__(self, project, ui):
        self.project = project
        self.ui = ui
        self.hebesatz_params = None
        self.rohmiete_params = None
        self.sachwert_params = None
        self.bauvolumen_params = None

    def load_content(self):
        self.project_frame = Projektrahmendaten.features(
            project=self.project)[0]
        self.gemeinden = Gemeinden.features(project=self.project)
        self.grst_settings = GrundsteuerSettings.features(create=True)
        if len(self.grst_settings) == 0:
            self.get_grst_base_settings()
        self.grst_settings = self.grst_settings[0]

        self.setup_hebesatz()
        self.setup_rohmiete()

    def get_grst_base_settings(self):
        gemeinden = self.project.basedata.get_table(
            'bkg_gemeinden', 'Basisdaten_deutschland').features()
        gem = gemeinden.get(AGS=self.project_frame.ags)
        is_new_bundesland = int(self.project_frame.ags) > 11000000
        attrs = {'Hebesatz_GrStB': gem.Hebesatz_GrStB,
                 'is_new_bundesland': is_new_bundesland}

        startwerte = self.project.basedata.get_table(
            'GrSt_Startwerte_Rohmieten_Bodenwert',
            'Einnahmen').features()
        gem_typ_startwerte = startwerte.get(Gemeindetyp=gem.Gemeindetyp)

        common_fields = set([f.name for f in startwerte.fields()]).intersection(
            [f.name for f in self.grst_settings.fields()])

        for field in common_fields:
            attrs[field] = gem_typ_startwerte[field]
        self.grst_settings.add(**attrs)

    def setup_hebesatz(self):
        if self.hebesatz_params:
            self.hebesatz_params.close()
        layout = self.ui.grundsteuer_hebesatz_param_group.layout()
        clear_layout(layout)
        self.params = Params(
            layout, help_file='einnahmen_grundsteuer_hebesatz.txt')

        self.params.add(Title('Rohmiete 1964 in Euro pro Monat', bold=False))

        self.params.hebesatz = Param(
            self.grst_settings.Hebesatz_GrStB,
            SpinBox(maximum=999, step=10),
            label='Hebesatz GrSt B Projektgemeinde',
            unit='v.H.'
        )

        def save():
            self.grst_settings.Hebesatz_GrStB = self.params.hebesatz.value
            self.grst_settings.save()

        self.params.show(title='Hebesatz bearbeiten')
        self.params.changed.connect(save)

    def setup_rohmiete(self):
        if self.rohmiete_params:
            self.rohmiete_params.close()
        layout = self.ui.grundsteuer_hebesatz_param_group.layout()
        clear_layout(layout)
        self.params = Params(
            layout, help_file='einnahmen_grundsteuer_rohmieten.txt')

        self.params.hebesatz = Param(
            self.grst_settings.Hebesatz_GrStB,
            SpinBox(maximum=999, step=10),
            label='Hebesatz GrSt B Projektgemeinde',
            unit='v.H.'
        )

        def save():
            self.grst_settings.Hebesatz_GrStB = self.params.hebesatz.value
            self.grst_settings.save()

        self.params.show(title='Rohmieten bearbeiten')
        self.params.changed.connect(save)

    def close(self):
        if self.hebesatz_params:
            self.hebesatz_params.close()
        if self.rohmiete_params:
            self.rohmiete_params.close()
        if self.sachwert_params:
            self.sachwert_params.close()
        if self.bauvolumen_params:
            self.bauvolumen_params.close()


class MunicipalTaxRevenue(Domain):
    """"""

    ui_label = 'kommunale Steuereinnahmen'
    ui_file = 'ProjektCheck_dockwidget_analysis_07-KSt.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_tax_1.png"
    layer_group = 'Wirkungsbereich 7 - Kommunale Steuereinnahmen'

    def setupUi(self):
        self.grundsteuer = Grundsteuer(self.project, self.ui)
        self.migration_ew = EinwohnerMigration(self.project, self.ui)
        self.migration_svb = BeschaeftigtenMigration(self.project, self.ui)

    def load_content(self):
        super().load_content()
        self.grundsteuer.load_content()
        self.migration_ew.load_content()
        self.migration_svb.load_content()

    def close(self):
        self.migration_ew.close()
        self.grundsteuer.close()
        self.migration_svb.close()
        super().close()