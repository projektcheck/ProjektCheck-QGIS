from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QObject, pyqtSignal
import numpy as np
from qgis import utils
import os

from projektcheck.base.domain import Domain
from projektcheck.base.project import ProjectLayer
from projektcheck.base.dialogs import ProgressDialog
from projektcheck.domains.municipaltaxrevenue.tables import (
    Gemeindebilanzen, EinwohnerWanderung, BeschaeftigtenWanderung,
    GrundsteuerSettings)
from projektcheck.domains.municipaltaxrevenue.migration import (
    EwMigrationCalculation, SvBMigrationCalculation, MigrationCalculation)
from projektcheck.domains.municipaltaxrevenue.tax import (
    GrundsteuerCalculation, EinkommensteuerCalculation,
    FamAusgleichCalculation, GewerbesteuerCalculation)
from projektcheck.domains.definitions.tables import (
    Projektrahmendaten, Teilflaechen)
from projektcheck.domains.constants import Nutzungsart
from projektcheck.utils.utils import clear_layout
from projektcheck.base.params import Params, Param, Title, Seperator
from projektcheck.base.inputs import DoubleSpinBox, SpinBox
from projektcheck.utils.utils import open_file


class Migration(QObject):
    changed = pyqtSignal()

    def __init__(self, project, ui, layer_group, canvas):
        super().__init__()
        self.layer_group = layer_group
        self.canvas = canvas
        self.project = project
        self.ui = ui
        self.params = None

    def load_content(self):
        self.project_frame = Projektrahmendaten.features(
            project=self.project)[0]
        self.gemeinden = Gemeindebilanzen.features()
        self.project_frame = Projektrahmendaten.features()[0]
        self.areas = Teilflaechen.features()

    def close(self):
        if self.params:
            self.params.close()


class EinwohnerMigration(Migration):

    def __init__(self, project, ui, layer_group, canvas):
        super().__init__(project, ui, layer_group, canvas)
        self.ui.migration_inhabitants_button.clicked.connect(self.calculate)

    def load_content(self):
        super().load_content()
        self.wanderung = EinwohnerWanderung.features(create=True)

        self.ui.einwohner_parameter_group.setVisible(False)
        if len(self.wanderung) == 0:
            self.ui.recalculate_inhabitants_check.setChecked(True)
            self.ui.recalculate_inhabitants_check.setVisible(False)
            self.ui.einwohner_parameter_group.setVisible(False)
        else:
            self.setup_params()

    def calculate(self):
        if not self.ui.recalculate_inhabitants_check.isChecked():
            self.add_layer()
            return
        sum_ew = sum(x or 0 for x in self.areas.values('ew'))
        if sum_ew == 0:
            QMessageBox.warning(self.ui, 'Fehler',
                                'Es wurden keine definierten Teilflächen mit '
                                'der Nutzungsart "Wohnen" gefunden.')
            return

        job = EwMigrationCalculation(self.project)

        def on_close():
            self.changed.emit()
            if not self.dialog.success:
                self.wanderung.table.truncate()
                self.ui.recalculate_inhabitants_check.setVisible(False)
                self.ui.recalculate_inhabitants_check.setChecked(True)
                return
            self.ui.recalculate_inhabitants_check.setVisible(True)
            self.ui.recalculate_inhabitants_check.setChecked(False)
            self.add_layer()
            self.setup_params()

        self.dialog = ProgressDialog(job, parent=self.ui, on_close=on_close)
        self.dialog.show()

    def setup_params(self):
        if self.params:
            self.params.close()
        self.ui.einwohner_parameter_group.setVisible(True)
        layout = self.ui.einwohner_parameter_group.layout()
        clear_layout(layout)
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
        project_saldo = Param(wanderung.saldo, spinbox, repr_format='%+.2f',
                              label=f' - {project_gem.GEN}', unit='Ew')
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
            param = Param(wanderung.saldo, spinbox, label=f' - {gemeinde.GEN}',
                          unit='Ew')
            self.params.add(param, name=ags)
            spinbox.changed.connect(lambda o, a=ags: update_salden(a))
            spinbox.locked.connect(lambda o, a=ags: update_salden(a))

        self.params.add(Seperator())

        self.params.add(Param(
            -factor_outer * sum_ew,
            label='Restliches Bundesgebiet / Ausland',
            unit='Ew'
        ))

        def save():
            self.wanderung.update_pandas(self.df_wanderung)
            self.changed.emit()
            self.canvas.refreshAllLayers()

        self.params.show(title='Geschätzte Salden (Einwohner) bearbeiten',
            scrollable=True)
        self.params.changed.connect(save)

    def add_layer(self):
        self.output = ProjectLayer.from_table(
            self.wanderung.table, groupname=self.layer_group)
        self.output.draw(
            label='Wanderungssalden Einwohner',
            style_file='einnahmen_einwohnerwanderung.qml',
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()


class BeschaeftigtenMigration(Migration):

    def __init__(self, project, ui, layer_group, canvas):
        super().__init__(project, ui, layer_group, canvas)
        self.ui.migration_jobs_button.clicked.connect(self.calculate)

    def load_content(self):
        super().load_content()
        self.wanderung = BeschaeftigtenWanderung.features(create=True)
        if len(self.wanderung) == 0:
            self.ui.recalculate_jobs_check.setChecked(True)
            self.ui.recalculate_jobs_check.setVisible(False)
            self.ui.svb_parameter_group.setVisible(False)
        else:
            self.setup_params()

    def calculate(self):
        if not self.ui.recalculate_jobs_check.isChecked():
            self.add_layer()
            return
        sum_ap = sum(x or 0 for x in self.areas.values('ap_gesamt'))
        if sum_ap == 0:
            # ToDo: actually there are just no jobs
            # (e.g. when manually set to zero)
            QMessageBox.warning(self.ui, 'Fehler',
                                'Es wurden keine definierten Teilflächen mit '
                                'der Nutzungsart "Gewerbe" gefunden.')
            return

        job = SvBMigrationCalculation(self.project)

        def on_close():
            self.changed.emit()
            if not self.dialog.success:
                self.wanderung.table.truncate()
                self.ui.recalculate_inhabitants_check.setVisible(False)
                self.ui.recalculate_inhabitants_check.setChecked(True)
                return
            self.ui.recalculate_jobs_check.setVisible(True)
            self.ui.recalculate_jobs_check.setChecked(False)
            self.add_layer()
            self.setup_params()

        self.dialog = ProgressDialog(job, parent=self.ui, on_close=on_close)
        self.dialog.show()

    def setup_params(self):
        if self.params:
            self.params.close()
        self.ui.svb_parameter_group.setVisible(True)
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
        sum_ap = sum(self.areas.values('ap_gesamt'))

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
        project_saldo = Param(wanderung.saldo, spinbox, repr_format='%+.2f',
                              label=f' - {project_gem.GEN}', unit='SvB')
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
            param = Param(wanderung.saldo, spinbox, label=f' - {gemeinde.GEN}',
                          unit='SvB')
            self.params.add(param, name=ags)
            spinbox.changed.connect(lambda o, a=ags: update_salden(a))
            spinbox.locked.connect(lambda o, a=ags: update_salden(a))

        self.params.add(Seperator())

        self.params.add(Param(
            -factor_outer * sum_ap,
            label='Restliches Bundesgebiet / Ausland',
            unit='SvB'
        ))

        def save():
            self.wanderung.update_pandas(self.df_wanderung)
            self.canvas.refreshAllLayers()

        self.params.show(title='Geschätzte Salden (Beschäftigte) bearbeiten',
                         scrollable=True)
        self.params.changed.connect(save)

    def add_layer(self):
        self.output = ProjectLayer.from_table(
            self.wanderung.table, groupname=self.layer_group)
        self.output.draw(
            label='Wanderungssalden Beschäftigte',
            style_file='einnahmen_beschaeftigtenwanderung.qml',
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()


class Grundsteuer(QObject):
    changed = pyqtSignal()

    def __init__(self, project, ui, layer_group):
        super().__init__()
        self.project = project
        self.ui = ui
        self.layer_group = layer_group

        self.ui.calc_grundsteuer_button.clicked.connect(self.calculate)

        self.hebesatz_params = None
        self.rohmiete_params = None
        self.sachwert_params = None
        self.bauvolumen_params = None

    def load_content(self):
        self.project_frame = Projektrahmendaten.features(
            project=self.project)[0]
        self.gemeinden = Gemeindebilanzen.features(project=self.project)
        self.grst_settings = GrundsteuerSettings.features(create=True)
        if len(self.grst_settings) == 0:
            self.get_grst_base_settings()
        self.grst_settings = self.grst_settings[0]
        self.areas = Teilflaechen.features(project=self.project)
        self.ew_wanderung = EinwohnerWanderung.features()
        self.svb_wanderung = BeschaeftigtenWanderung.features()

        self.setup_hebesatz()
        self.setup_rohmiete()
        self.setup_sachwert()
        self.setup_bauvolumen()

    def get_grst_base_settings(self):
        gemeinden = self.project.basedata.get_table(
            'bkg_gemeinden', 'Basisdaten_deutschland').features()
        gem = gemeinden.get(AGS=self.project_frame.ags)
        is_new_bundesland = int(self.project_frame.ags) >= 11000000
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
        self.hebesatz_params = Params(
            layout, help_file='einnahmen_grundsteuer_hebesatz.txt')

        self.hebesatz_params.hebesatz = Param(
            self.grst_settings.Hebesatz_GrStB,
            SpinBox(maximum=999, step=10),
            label='Hebesatz GrSt B Projektgemeinde',
            unit='v.H.'
        )

        def save():
            self.changed.emit()
            self.grst_settings.Hebesatz_GrStB = \
                self.hebesatz_params.hebesatz.value
            self.grst_settings.save()

        self.hebesatz_params.show(title='Hebesatz bearbeiten')
        self.hebesatz_params.changed.connect(save)

    def setup_rohmiete(self):
        tou = self.areas.values('nutzungsart')
        if self.grst_settings.is_new_bundesland \
           or not Nutzungsart.WOHNEN.value in tou:
            self.ui.grundsteuer_rohmiete_param_group.setVisible(False)
            return
        self.ui.grundsteuer_rohmiete_param_group.setVisible(True)
        if self.rohmiete_params:
            self.rohmiete_params.close()
        layout = self.ui.grundsteuer_rohmiete_param_group.layout()
        clear_layout(layout)
        self.rohmiete_params = Params(
            layout, help_file='einnahmen_grundsteuer_rohmieten.txt')

        self.rohmiete_params.add(Title('Rohmiete 1964 in Euro pro Monat',
                                       bold=False))

        self.rohmiete_params.efh = Param(
            self.grst_settings.EFH_Rohmiete / 100,
            DoubleSpinBox(minimum=0.3, maximum=5, step=0.05),
            label=f' - Einfamilienhaus',
            unit='€/m²'
        )
        self.rohmiete_params.dhh = Param(
            self.grst_settings.DHH_Rohmiete / 100,
            DoubleSpinBox(minimum=0.3, maximum=5, step=0.05),
            label=f' - Doppelhaus',
            unit='€/m²'
        )
        self.rohmiete_params.rhw = Param(
            self.grst_settings.RHW_Rohmiete / 100,
            DoubleSpinBox(minimum=0.3, maximum=5, step=0.05),
            label=f' - Reihenhaus',
            unit='€/m²'
        )
        self.rohmiete_params.mfh = Param(
            self.grst_settings.MFH_Rohmiete / 100,
            DoubleSpinBox(minimum=0.3, maximum=5, step=0.05),
            label=f' - Mehrfamilienhaus',
            unit='€/m²'
        )

        def save():
            self.changed.emit()
            self.grst_settings.EFH_Rohmiete = round(
                self.rohmiete_params.efh.value * 100)
            self.grst_settings.DHH_Rohmiete = round(
                self.rohmiete_params.dhh.value * 100)
            self.grst_settings.RHW_Rohmiete = round(
                self.rohmiete_params.rhw.value * 100)
            self.grst_settings.MFH_Rohmiete = round(
                self.rohmiete_params.mfh.value * 100)
            self.grst_settings.save()

        self.rohmiete_params.show(title='Rohmieten bearbeiten')
        self.rohmiete_params.changed.connect(save)

    def setup_sachwert(self):
        tou = self.areas.values('nutzungsart')
        if not self.grst_settings.is_new_bundesland\
           or not Nutzungsart.WOHNEN.value in tou:
            self.ui.grundsteuer_sachwert_param_group.setVisible(False)
            return
        if self.sachwert_params:
            self.sachwert_params.close()
        self.ui.grundsteuer_sachwert_param_group.setVisible(True)
        layout = self.ui.grundsteuer_sachwert_param_group.layout()
        clear_layout(layout)
        self.sachwert_params = Params(
            layout, help_file='einnahmen_grundsteuer_sachwertverfahren.txt')

        self.sachwert_params.add(Title('Sachwertverfahren', bold=False))
        self.sachwert_params.bodenwert = Param(
            self.grst_settings.Bodenwert_SWV / 100,
            DoubleSpinBox(minimum=0.3, maximum=5, step=0.05),
            label=f' - Bodenwert 1935 pro m²',
            unit='€/m²'
        )
        self.sachwert_params.flaeche = Param(
            self.grst_settings.qm_Grundstueck_pro_WE_EFH,
            SpinBox(minimum=300, maximum=2000, step=1),
            label=f' - mittl. Größe Einfamilienhausgrundstücke',
            unit='m²'
        )

        def save():
            self.changed.emit()
            self.grst_settings.Bodenwert_SWV = round(
                self.sachwert_params.bodenwert.value * 100)
            self.grst_settings.qm_Grundstueck_pro_WE_EFH = \
                self.sachwert_params.flaeche.value
            self.grst_settings.save()

        self.sachwert_params.show(title='Sachwertverfahren bearbeiten')
        self.sachwert_params.changed.connect(save)

    def setup_bauvolumen(self):
        tou = self.areas.values('nutzungsart')
        if not (Nutzungsart.GEWERBE.value in tou or
                Nutzungsart.EINZELHANDEL.value in tou):
            self.ui.grundsteuer_bauvolumen_param_group.setVisible(False)
            # set to 0 as a precaution to not put some old values into
            # the calculation
            self.grst_settings.Bueroflaeche = 0
            self.grst_settings.Verkaufsraeume = 0
            self.grst_settings.save()
            return
        self.ui.grundsteuer_bauvolumen_param_group.setVisible(True)
        if self.bauvolumen_params:
            self.bauvolumen_params.close()
        layout = self.ui.grundsteuer_bauvolumen_param_group.layout()
        clear_layout(layout)
        self.bauvolumen_params = Params(
            layout, help_file='einnahmen_grundsteuer_bauvolumen.txt')

        self.bauvolumen_params.add(
            Title('Gewerbe / Einzelhandel: Voraussichtliches '
                  'Bauvolumen\n(Brutto-Grundfläche, BGF)', bold=False))

        self.bauvolumen_params.bueroflaeche = Param(
            self.grst_settings.Bueroflaeche,
            SpinBox(minimum=0, maximum=99999, step=10),
            label=f' - Bürofläche',
            unit='m²'
        )
        self.bauvolumen_params.verkaufsraeume = Param(
            self.grst_settings.Verkaufsraeume,
            SpinBox(minimum=0, maximum=99999, step=10),
            label=f' - Hallen und Verkaufsräume',
            unit='m²'
        )

        def save():
            self.changed.emit()
            self.grst_settings.Bueroflaeche = \
                self.bauvolumen_params.bueroflaeche.value
            self.grst_settings.Verkaufsraeume = \
                self.bauvolumen_params.verkaufsraeume.value
            self.grst_settings.save()

        self.bauvolumen_params.show(
            title='Voraussichtliches Bauvolumen bearbeiten')
        self.bauvolumen_params.changed.connect(save)

    def calculate(self):
        #if len(self.ew_wanderung) == 0 and len(self.svb_wanderung) == 0:
            #QMessageBox.warning(
                #self.ui, 'Fehler',
                #'Bitte führen Sie zunächst die Schätzung der Wanderungssalden '
                #'(Einwohner und/oder Beschäftige) durch.')
            #return

        job = GrundsteuerCalculation(self.project)

        def on_success(r):
            self.add_layer()

        self.changed.emit()
        self.dialog = ProgressDialog(job, parent=self.ui, on_success=on_success,
                                     auto_close=True)
        self.dialog.show()

    def add_layer(self):
        self.output = ProjectLayer.from_table(
            self.gemeinden.table, groupname=self.layer_group)
        self.output.draw(
            label='Grundsteuer',
            style_file='einnahmen_grundsteuer.qml',
            filter="grundsteuer != 'NULL'",
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()

    def close(self):
        if self.hebesatz_params:
            self.hebesatz_params.close()
        if self.rohmiete_params:
            self.rohmiete_params.close()
        if self.sachwert_params:
            self.sachwert_params.close()
        if self.bauvolumen_params:
            self.bauvolumen_params.close()


class Gewerbesteuer(QObject):
    changed = pyqtSignal()

    def __init__(self, project, ui, layer_group):
        super().__init__()
        self.layer_group = layer_group
        self.project = project
        self.ui = ui
        self.ui.calc_gewerbesteuer_button.clicked.connect(self.calculate)
        self.params = None

    def load_content(self):
        self.gemeinden = Gemeindebilanzen.features(project=self.project)
        self.setup_params()

    def setup_params(self):
        if self.params:
            self.params.close()
        layout = self.ui.gewerbesteuer_hebesatz_param_group.layout()
        clear_layout(layout)
        self.params = Params(
            layout, help_file='einnahmen_gewerbesteuer_hebesätze.txt')

        self.params.add(Title('Hebesätze', bold=False))

        for gemeinde in sorted(self.gemeinden, key=lambda x: x.GEN):
            spinbox = SpinBox(minimum=0, maximum=999, step=1)
            param = Param(gemeinde.Hebesatz_GewSt, spinbox,
                          label=f' - {gemeinde.GEN}',
                          unit='v.H.')
            self.params.add(param, name=gemeinde.AGS)

        def save():
            self.changed.emit()
            for gemeinde in self.gemeinden:
                param = self.params[gemeinde.AGS]
                gemeinde.Hebesatz_GewSt = param.value
                gemeinde.save()

        self.params.show(title='Hebesätze Gewerbesteuer bearbeiten',
                         scrollable=True)
        self.params.changed.connect(save)

    def calculate(self):
        if len(BeschaeftigtenWanderung.features()) == 0:
            QMessageBox.warning(
                self.ui, 'Fehler',
                'Bitte führen Sie zunächst die Schätzung der Wanderungssalden '
                '(Beschäftigte) durch.')
            return
        job = GewerbesteuerCalculation(self.project)

        def on_success(r):
            self.add_layer()

        self.changed.emit()
        self.dialog = ProgressDialog(job, parent=self.ui, on_success=on_success,
                                     auto_close=True)
        self.dialog.show()

    def add_layer(self):
        self.output = ProjectLayer.from_table(
            self.gemeinden.table, groupname=self.layer_group)
        self.output.draw(
            label='Gewerbesteuer',
            style_file='einnahmen_gewerbesteuer.qml',
            filter="gewerbesteuer != 'NULL'",
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()

    def close(self):
        if self.params:
            self.params.close()


class MunicipalTaxRevenue(Domain):
    """"""
    radius = 25000

    ui_label = 'Kommunale Steuereinnahmen'
    ui_file = 'domain_07-KSt.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_tax_1.png"
    layer_group = 'Wirkungsbereich 6 - Kommunale Steuereinnahmen'

    def setupUi(self):
        self.migration_ew = EinwohnerMigration(
            self.project, self.ui, self.layer_group, self.canvas)
        self.migration_svb = BeschaeftigtenMigration(
            self.project, self.ui, self.layer_group, self.canvas)
        self.grundsteuer = Grundsteuer(self.project, self.ui, self.layer_group)
        self.gewerbesteuer = Gewerbesteuer(self.project, self.ui,
                                           self.layer_group)
        self.areas = Teilflaechen.features()

        manual_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Kommunale_Steuereinnahmen.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(manual_path))
        result_help_path = os.path.join(
            self.settings.HELP_PATH,
            'Hinweise_zur_Ergebnisinterpretation_Kommunale_Einnahmen.pdf')
        self.ui.result_help_button.clicked.connect(
            lambda: open_file(result_help_path))

        self.ui.calc_einkommensteuer_button.clicked.connect(
            self.calc_einkommensteuer)
        self.ui.calc_fla_button.clicked.connect(
            self.calc_fam_ausgleich)
        self.ui.calc_umsatzsteuer_button.clicked.connect(
            self.calc_umsatzsteuer)
        self.ui.calc_gesamtsumme_button.clicked.connect(
            self.calc_gesamtsumme)

        self.migration_ew.changed.connect(
            lambda: self.reset_results(
                fields=['grundsteuer', 'einkommensteuer',
                        'fam_leistungs_ausgleich', 'summe_einnahmen']))
        self.migration_svb.changed.connect(
            lambda: self.reset_results(
                fields=['gewerbesteuer', 'umsatzsteuer', 'summe_einnahmen']))
        self.grundsteuer.changed.connect(
            lambda: self.reset_results(
                fields=['grundsteuer', 'summe_einnahmen']))
        self.gewerbesteuer.changed.connect(
            lambda: self.reset_results(
                fields=['gewerbesteuer', 'umsatzsteuer', 'summe_einnahmen']))

    def load_content(self):
        super().load_content()
        self.project_frame = Projektrahmendaten.features(
            project=self.project)[0]
        self.gemeinden = Gemeindebilanzen.features(create=True)
        if len(self.gemeinden) == 0:
            self.get_gemeinden()

        self.migration_ew.load_content()
        self.migration_svb.load_content()
        self.grundsteuer.load_content()
        self.gewerbesteuer.load_content()

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

    def calc_einkommensteuer(self):
        if len(self.migration_ew.wanderung) == 0:
            QMessageBox.warning(
                self.ui, 'Fehler',
                'Bitte führen Sie zunächst die Schätzung der Wanderungssalden '
                '(Einwohner) durch.')
            return
        job = EinkommensteuerCalculation(self.project)

        def on_success(r):
            self.add_est_layer()

        self.reset_results(fields=['fam_leistungs_ausgleich',
                                   'summe_einnahmen'])
        self.dialog = ProgressDialog(job, parent=self.ui, on_success=on_success,
                                     auto_close=True)
        self.dialog.show()

    def calc_fam_ausgleich(self):
        if sum([abs(gem.einkommensteuer) for gem in self.gemeinden]) == 0:
            QMessageBox.warning(
                self.ui, 'Fehler',
                'Bitte führen Sie zunächst die Schätzung der Einkommensteuer '
                'durch.')
            return
        job = FamAusgleichCalculation(self.project)

        def on_success(r):
            self.add_fla_layer()

        self.reset_results(fields=['summe_einnahmen'])
        self.dialog = ProgressDialog(job, parent=self.ui, on_success=on_success,
                                     auto_close=True)
        self.dialog.show()

    def calc_umsatzsteuer(self):
        if sum([abs(gem.gewerbesteuer) for gem in self.gemeinden]) == 0:
            QMessageBox.warning(
                self.ui, 'Fehler',
                'Bitte führen Sie zunächst die Schätzung der Gewerbesteuer '
                'durch.')
            return
        ust_base = self.basedata.get_table(
            'USt_Kennwerte', 'Einnahmen').features()[0]
        factor_gst = ust_base.GemAnt_USt_EUR_pro_EUR_GewSt
        factor_svb = ust_base.GemANt_USt_EUR_pro_SvB
        for gem in self.gemeinden:
            wanderung = self.migration_svb.wanderung.get(AGS=gem.AGS)
            saldo = wanderung.saldo if wanderung else 0
            ust = factor_gst * gem.gewerbesteuer + factor_svb * saldo
            rnd = 1000 if ust >= 500 else 100
            ust = round(ust/rnd) * rnd
            gem.umsatzsteuer = ust
            gem.save()
        self.reset_results(fields=['summe_einnahmen'])
        self.add_ust_layer()

    def calc_gesamtsumme(self):
        tou = self.areas.values('nutzungsart')
        if (Nutzungsart.WOHNEN.value in tou and
            sum([abs(gem.fam_leistungs_ausgleich)
                 for gem in self.gemeinden]) == 0):
            QMessageBox.warning(
                self.ui, 'Fehler',
                'Bitte führen Sie zunächst die Schätzung des '
                'Familienleistungsausgleichs durch.')
            return
        if ((Nutzungsart.GEWERBE.value in tou or
            Nutzungsart.EINZELHANDEL.value in tou) and
            sum([abs(gem.umsatzsteuer) for gem in self.gemeinden]) == 0):
            QMessageBox.warning(
                self.ui, 'Fehler',
                'Bitte führen Sie zunächst die Schätzung der Umsatzsteuer '
                'durch.')
            return
        for gem in self.gemeinden:
            gem.summe_einnahmen = (gem.grundsteuer + gem.einkommensteuer +
                                   gem.gewerbesteuer + gem.umsatzsteuer +
                                   gem.fam_leistungs_ausgleich)
            gem.save()
        self.add_gesamt_layer()

    def add_est_layer(self):
        self.output = ProjectLayer.from_table(
            self.gemeinden.table, groupname=self.layer_group)
        self.output.draw(
            label='Einkommensteuer',
            style_file='einnahmen_einkommensteuer.qml',
            filter="einkommensteuer != 'NULL'",
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()

    def add_fla_layer(self):
        self.output = ProjectLayer.from_table(
            self.gemeinden.table, groupname=self.layer_group)
        self.output.draw(
            label='Familienleistungsausgleich',
            style_file='einnahmen_fam_leistungs_ausgleich.qml',
            filter="fam_leistungs_ausgleich != 'NULL'",
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()

    def add_ust_layer(self):
        self.output = ProjectLayer.from_table(
            self.gemeinden.table, groupname=self.layer_group)
        self.output.draw(
            label='Umsatzsteuer',
            style_file='einnahmen_umsatzsteuer.qml',
            filter="umsatzsteuer != 'NULL'",
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()

    def add_gesamt_layer(self):
        self.output = ProjectLayer.from_table(
            self.gemeinden.table, groupname=self.layer_group)
        self.output.draw(
            label='Gesamtsumme Einnahmen',
            style_file='einnahmen_summe_einnahmen.qml',
            filter="summe_einnahmen != 'NULL'",
            uncheck_siblings=True, redraw=False
        )
        self.output.zoom_to()

    @classmethod
    def reset_results(cls, fields=['grundsteuer', 'einkommensteuer',
                                   'gewerbesteuer', 'umsatzsteuer',
                                   'fam_leistungs_ausgleich',
                                   'summe_einnahmen']):
        bilanzen = Gemeindebilanzen.features(create=True)
        df_bilanzen = bilanzen.to_pandas()
        for field in fields:
            df_bilanzen[field] = None
        bilanzen.update_pandas(df_bilanzen)
        canvas = utils.iface.mapCanvas()
        canvas.refreshAllLayers()

    @classmethod
    def reset_gewerbe_einzelhandel(cls):
        BeschaeftigtenWanderung.get_table(create=True).truncate()
        cls.reset_results(fields=['grundsteuer', 'gewerbesteuer','umsatzsteuer',
                                  'summe_einnahmen'])

    @classmethod
    def reset_wohnen(cls):
        EinwohnerWanderung.get_table(create=True).truncate()
        cls.reset_results(fields=['grundsteuer', 'fam_leistungs_ausgleich',
                                  'einkommensteuer', 'summe_einnahmen'])

    def close(self):
        self.migration_ew.close()
        self.grundsteuer.close()
        self.migration_svb.close()
        self.gewerbesteuer.close()
        super().close()