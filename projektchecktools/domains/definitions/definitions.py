import pandas as pd
import numpy as np
import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QSpacerItem, QSizePolicy

from projektchecktools.base.tools import MapClickedTool
from projektchecktools.base.inputs import (SpinBox, ComboBox, LineEdit,
                                           Checkbox, Slider, DoubleSpinBox)
from projektchecktools.base.params import (Params, Param, Title,
                                           Seperator, SumDependency)
from projektchecktools.base.domain import Domain, Worker
from projektchecktools.base.project import ProjectLayer
from projektchecktools.utils.utils import clear_layout
from projektchecktools.domains.traffic.traffic import Traffic
from projektchecktools.domains.traffic.tables import Connectors
from projektchecktools.domains.definitions.tables import (
    Teilflaechen, Verkaufsflaechen, Wohneinheiten,
    Gewerbeanteile, Projektrahmendaten)
from projektchecktools.domains.jobs_inhabitants.tables import (
    ApProJahr, WohnenProJahr, WohnenStruktur)
from projektchecktools.utils.utils import open_file
from projektchecktools.base.dialogs import ProgressDialog


class TrafficConnectors:
    layer_group = 'Projektdefinition'

    def __init__(self, ui, canvas, project):
        self.project = project
        self.canvas = canvas
        self.connector_tool = MapClickedTool(ui.connector_button,
                                             canvas=canvas,
                                             target_epsg=project.settings.EPSG)
        self.connector_tool.map_clicked.connect(self.map_clicked)

    def load_content(self, area):
        self.connectors = Connectors.features(create=False,
                                              project=self.project)
        self.show_connectors()
        self.toggle_connector(area)

    def show_connectors(self):
        self.output = ProjectLayer.from_table(
            Connectors.get_table(), groupname=self.layer_group)
        self.output.draw(
            label='Anbindungspunkte',
            style_file='verkehr_anbindungspunkte.qml', prepend=True)

    def toggle_connector(self, area=None):
        self.connector = None
        layer = self.output.layer
        if not layer:
            return
        layer.removeSelection()
        if area:
            self.connector = self.connectors.get(id_teilflaeche=area.id)
            layer.select(self.connector.id)

    def map_clicked(self, geom):
        if not self.connector:
            return
        self.connector.geom = geom
        self.canvas.refreshAllLayers()
        self.connector.save()

    def close(self):
        self.connector_tool.set_active(False)
        if hasattr(self, 'output'):
            layer = self.output.layer
            if layer:
                layer.removeSelection()


class WohnenDevelopment(Worker):
    BETRACHTUNGSZEITRAUM_JAHRE = 25

    def __init__(self, basedata, area, parent=None):
        super().__init__(parent=parent)
        self.area = area
        self.wohnen_struktur = WohnenStruktur.features(create=True)
        self.wohnen_pro_jahr = WohnenProJahr.features(create=True)
        self.wohneinheiten = Wohneinheiten.features()
        self.gebaeudetypen_base = basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        ).features()
        self.einwohner_base = basedata.get_table(
            'Einwohner_pro_WE', 'Bewohner_Arbeitsplaetze'
        )

    def work(self):
        self.log('Berechne Bevölkerungsentwicklung...')
        self.set_development()
        self.set_progress(80)
        self.log('Berechne Anzahl der Wege...')
        self.set_ways()

    def set_development(self):
        begin = self.area.beginn_nutzung
        duration = self.area.aufsiedlungsdauer
        end = begin + self.BETRACHTUNGSZEITRAUM_JAHRE - 1

        df_einwohner_base = self.einwohner_base.to_pandas()
        df_wohneinheiten_tfl = self.wohneinheiten.filter(
            id_teilflaeche=self.area.id).to_pandas()

        wohnen_struktur_tfl = self.wohnen_struktur.filter(
            id_teilflaeche=self.area.id)
        wohnen_struktur_tfl.delete()
        wohnen_pro_jahr_tfl = self.wohnen_pro_jahr.filter(
            id_teilflaeche=self.area.id)
        wohnen_pro_jahr_tfl.delete()

        df_wohnen_struktur = wohnen_struktur_tfl.to_pandas()

        flaechen_template = pd.DataFrame()
        geb_types = df_wohneinheiten_tfl['id_gebaeudetyp'].values
        flaechen_template['id_gebaeudetyp'] = geb_types
        flaechen_template['id_teilflaeche'] = self.area.id
        flaechen_template['wohnungen'] = list(
                df_wohneinheiten_tfl['we'].values.astype(float) *
                df_wohneinheiten_tfl['ew_je_we'] /
                duration)
        for j in range(begin, end + 1):
            for i in range(1, duration + 1):
                if j - begin + i - duration + 1 > 0:
                    df = flaechen_template.copy()
                    df['jahr'] = j
                    df['alter_we'] = j - begin + i - duration + 1
                    df_wohnen_struktur = df_wohnen_struktur.append(df)

        self.wohnen_struktur.update_pandas(df_wohnen_struktur)

        # Apply weight factor based on user-defined proportion of persons < 18
        for bt in self.gebaeudetypen_base:
            base_factor_u18 = float(bt.default_anteil_u18)
            user_factor_u18 = df_wohneinheiten_tfl[
                    df_wohneinheiten_tfl['id_gebaeudetyp']==bt.IDGebaeudetyp]
            user_factor_u18 = user_factor_u18['anteil_u18'].values[0]
            weight_u18 = user_factor_u18 / base_factor_u18
            weight_o18 = (100 - user_factor_u18) / (100 - base_factor_u18)
            df_einwohner_base.loc[
                (df_einwohner_base['IDAltersklasse'] == 1) &
                (df_einwohner_base['IDGebaeudetyp'] == bt.IDGebaeudetyp),
                ["Einwohner"]] *= weight_u18
            df_einwohner_base.loc[
                (df_einwohner_base['IDAltersklasse'] > 1) &
                (df_einwohner_base['IDGebaeudetyp'] == bt.IDGebaeudetyp),
                ["Einwohner"]] *= weight_o18

        # prepare the base table, take duration as age reference for development
        # over years
        df_einwohner_base['reference'] = 1
        for geb_typ, group in df_einwohner_base.groupby('IDGebaeudetyp'):
            reference = group[group['AlterWE'] == 3]['Einwohner'].sum()
            df_einwohner_base.loc[df_einwohner_base['IDGebaeudetyp'] == geb_typ,
                                  'reference'] = reference

        # fun with great column names in base data
        df_einwohner_base.rename(columns={'Jahr': 'jahr',
                                          'IDGebaeudetyp': 'id_gebaeudetyp',
                                          'AlterWE': 'alter_we',
                                          'Altersklasse': 'altersklasse',
                                          'IDAltersklasse': 'id_altersklasse',},
                                 inplace=True)

        joined = df_wohnen_struktur.merge(df_einwohner_base, how='left',
                                          on=['id_gebaeudetyp', 'alter_we'])
        grouped = joined.groupby(['jahr', 'id_altersklasse'])
        # make an appendable copy of the (empty) bewohner dataframe
        df_wohnen_pro_jahr = wohnen_pro_jahr_tfl.to_pandas()
        group_template = df_wohnen_pro_jahr.copy()

        for idx, group in grouped:
            entry = group_template.copy()
            # corresponding SQL:  Sum([Einwohner]*[Wohnungen])
            n_bewohner = (group['wohnungen'] * group['Einwohner']
                          / group['reference']).sum()
            entry['bewohner'] = [n_bewohner]
            entry['id_altersklasse'] = group['id_altersklasse'].unique()
            entry['altersklasse'] = group['altersklasse'].unique()
            entry['jahr'] = group['jahr'].unique()
            entry['id_teilflaeche'] = self.area.id
            df_wohnen_pro_jahr = df_wohnen_pro_jahr.append(entry)

        self.wohnen_pro_jahr.update_pandas(df_wohnen_pro_jahr)


    def set_ways(self):
        df_wohneinheiten = self.wohneinheiten.filter(
            id_teilflaeche=self.area.id).to_pandas()
        df_gebaeudetypen = self.gebaeudetypen_base.to_pandas()
        df_gebaeudetypen.rename(columns={'IDGebaeudetyp': 'id_gebaeudetyp'},
                                inplace=True)
        joined = df_wohneinheiten.merge(df_gebaeudetypen, on='id_gebaeudetyp')

        n_ew = joined['ew_je_we'] * joined['we']
        n_ways = n_ew * joined['Wege_je_Einwohner']
        n_ways_miv = n_ways * joined['Anteil_Pkw_Fahrer'] / 100

        self.area.wege_gesamt = int(n_ways.sum())
        self.area.wege_miv = int(n_ways_miv.sum())

        self.area.save()


class Wohnen:

    def __init__(self, basedata, layout):
        self.basedata = basedata
        self.gebaeudetypen_base = basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        ).features()
        self.df_presets = basedata.get_table(
            'WE_nach_Gebietstyp', 'Definition_Projekt'
        ).to_pandas()
        self.wohneinheiten = Wohneinheiten.features(create=True)
        self.layout = layout

    def setup_params(self, area):
        self.area = area
        clear_layout(self.layout)
        self.params = Params(self.layout,
                             help_file='definitionen_wohnen.txt')
        self.params.add(Title('Bezugszeitraum'))
        self.params.beginn_nutzung = Param(
            area.beginn_nutzung, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges', repr_format='%d'
        )
        self.params.aufsiedlungsdauer = Param(
            area.aufsiedlungsdauer, SpinBox(minimum=1, maximum=100),
            label='Dauer des Bezuges', unit='Jahr(e)')
        self.params.add(Seperator())

        self.params.add(Title('Anzahl Wohneinheiten nach Gebäudetypen'))

        preset_names = np.unique(self.df_presets['Gebietstyp'].values)
        options = ['Gebietstyp wählen'] + list(preset_names)
        self.preset_combo = ComboBox(options)
        self.preset_combo.input.model().item(0).setEnabled(False)

        param = Param(0, self.preset_combo, label='Vorschlagswerte')
        param.hide_in_overview = True
        self.params.add(param, name='gebietstyp')
        self.params.add(
            QSpacerItem(0, 3, QSizePolicy.Fixed, QSizePolicy.Minimum))

        def preset_changed(gebietstyp):
            presets = self.df_presets[self.df_presets['Gebietstyp']==gebietstyp]
            for idx, preset in presets.iterrows():
                id_bt = preset['IDGebaeudetyp']
                bt = self.gebaeudetypen_base.get(id=id_bt)
                param = self.params.get(bt.param_we)
                param.input.value = self.area.area * preset['WE_pro_Hektar']

        self.preset_combo.changed.connect(preset_changed)

        for bt in self.gebaeudetypen_base:
            param_name = bt.param_we
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            value = feature.we if feature else 0
            slider = Slider(maximum=999)
            self.params.add(Param(
                value, slider,
                label=f'... in {bt.display_name}'),
                name=param_name
            )
            slider.changed.connect(
                lambda: self.preset_combo.set_value(options[0]))

        self.params.add(Seperator())

        self.params.add(Title('Mittlere Anzahl Einwohner pro Wohneinheit\n'
                              '(3 Jahre nach Bezug)'))

        for bt in self.gebaeudetypen_base:
            param_name = bt.param_ew_je_we
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            # set to default if no feature yet
            value = feature.ew_je_we if feature else bt.default_ew_je_we
            self.params.add(Param(
                value, DoubleSpinBox(step=0.1, maximum=50),
                label=f'... in {bt.display_name}'),
                name=param_name
            )

        self.params.add(Seperator())

        self.params.add(Title('Anteil an unter 18 Jährigen'))

        for bt in self.gebaeudetypen_base:
            param_name = bt.param_anteil_u18
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            # set to default if no feature yet
            value = feature.anteil_u18 if feature else bt.default_anteil_u18
            self.params.add(Param(
                value, Slider(maximum=60), unit='%',
                label=f'... in {bt.display_name}'),
                name=param_name
            )

        self.params.changed.connect(self.save)
        self.params.show(
            title='Wohnen: Bezugszeitraum und Maß der baulichen Nutzung')

    def save(self):
        we_sum = 0
        for bt in self.gebaeudetypen_base:
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            if not feature:
                feature = self.wohneinheiten.add(
                    id_gebaeudetyp=bt.id, id_teilflaeche=self.area.id)
            we = getattr(self.params, bt.param_we).value
            feature.we = we
            we_sum += we
            ew_je_we = getattr(self.params, bt.param_ew_je_we).value
            feature.ew_je_we = ew_je_we
            anteil_u18 = getattr(self.params, bt.param_anteil_u18).value
            feature.anteil_u18 = anteil_u18
            cor_factor = ew_je_we / bt.Ew_pro_WE_Referenz
            feature.korrekturfaktor = cor_factor
            feature.name_gebaeudetyp = bt.NameGebaeudetyp
            feature.save()

        self.area.beginn_nutzung = self.params.beginn_nutzung.value
        self.area.aufsiedlungsdauer = self.params.aufsiedlungsdauer.value
        self.area.we_gesamt = we_sum

        Traffic.reset()

        self.area.save()

        job = WohnenDevelopment(self.basedata, self.area)

        dialog = ProgressDialog(
            job, auto_close=True,
            parent=self.layout.parentWidget())
        dialog.show()

    def clear(self, area):
        self.wohneinheiten.filter(id_teilflaeche=area.id).delete()
        area.we_gesamt = None
        area.save()

    def close(self):
        if hasattr(self, 'params'):
            self.params.close()


class Gewerbe:
    # Default Gewerbegebietstyp
    DEFAULT_INDUSTRY_ID = 2
    BETRACHTUNGSZEITRAUM_JAHRE = 15

    def __init__(self, basedata, layout):
        self.layout = layout
        self.gewerbeanteile = Gewerbeanteile.features(create=True)
        self.ap_nach_jahr = ApProJahr.features(create=True)
        self.projektrahmendaten = Projektrahmendaten.features()
        self.basedata = basedata

        self.branchen = list(basedata.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt'
        ).features().filter(ID_Branche_ProjektCheck__gt=0))

        presets = basedata.get_table(
            'Vorschlagswerte_Branchenstruktur', 'Definition_Projekt'
        )
        self.df_presets_base = presets.to_pandas()

        density = basedata.get_table(
            'Dichtekennwerte_Gewerbe', 'Definition_Projekt'
        )
        self.df_density_base = density.to_pandas()

        industry_types = basedata.get_table(
            'Gewerbegebietstypen', 'Definition_Projekt'
        )
        self.df_industry_types_base = industry_types.to_pandas()

        default_idx = self.df_industry_types_base['IDGewerbegebietstyp'] == \
            self.DEFAULT_INDUSTRY_ID
        self.df_industry_types_base.loc[
            default_idx, 'Name_Gewerbegebietstyp'] += ' (default)'

    def set_industry_presets(self, preset_id):
        """set all branche values to db-presets of given gewerbe-id"""
        if preset_id == -1:
            return
        idx = self.df_presets_base['IDGewerbegebietstyp'] == preset_id
        presets = self.df_presets_base[idx]
        for branche in self.branchen:
            param = getattr(self.params, branche.param_gewerbenutzung)
            p_idx = presets['ID_Branche_ProjektCheck'] == branche.id
            preset = int(presets[p_idx]['Vorschlagswert_in_Prozent'].values[0])
            param.value = preset

    def estimate_jobs(self):
        """calculate estimation of number of jobs
        sets estimated jobs to branchen"""
        gemeindetyp = self.area.gemeinde_typ
        df_kennwerte = self.df_density_base[
            self.df_density_base['Gemeindetyp_ProjektCheck'] == gemeindetyp]

        jobs_sum = 0
        for branche in self.branchen:
            param = getattr(self.params, branche.param_gewerbenutzung)
            idx = df_kennwerte['ID_Branche_ProjektCheck'] == branche.id
            jobs_per_ha = int(df_kennwerte[idx]['AP_pro_ha_brutto'].values[0])
            jobs_ind = round(self.area.area * (param.input.value / 100.)
                             * jobs_per_ha)
            branche.estimated_jobs = jobs_ind
            branche.jobs_per_ha = jobs_per_ha
            jobs_sum += jobs_ind

        return jobs_sum

    def setup_params(self, area):
        self.area = area
        clear_layout(self.layout)
        self.params = Params(self.layout,
                             help_file='definitionen_gewerbe.txt')

        self.params.add(Title('Bezugszeitraum'))
        self.params.beginn_nutzung = Param(
            area.beginn_nutzung, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges', repr_format='%d'
        )
        self.params.aufsiedlungsdauer = Param(
            area.aufsiedlungsdauer, SpinBox(minimum=1, maximum=100),
            label='Dauer des Bezuges (Jahre, 1 = Bezug wird noch\n'
            'im Jahr des Bezugsbeginns abgeschlossen)', unit='Jahr(e)'
        )

        self.params.add(Seperator(margin=10))

        self.params.add(
            Title('Voraussichtlicher Anteil der Branchen an der Nettofläche'))

        preset_names = self.df_industry_types_base[
            'Name_Gewerbegebietstyp'].values
        preset_ids = self.df_industry_types_base['IDGewerbegebietstyp'].values
        options = ['Gebietstyp wählen'] + list(preset_names)
        self.preset_combo = ComboBox(options, [-1] + list(preset_ids))
        self.preset_combo.input.model().item(0).setEnabled(False)
        param = Param(0, self.preset_combo, label='Vorschlagswerte')
        param.hide_in_overview = True
        self.params.add(param, name='gebietstyp')
        # break grid layout
        self.params.add(
            QSpacerItem(0, 3, QSizePolicy.Fixed, QSizePolicy.Minimum))

        def values_changed():
            if self.auto_check.value:
                n_jobs = self.estimate_jobs()
                self.ap_slider.set_value(n_jobs)

        def slider_changed():
            self.preset_combo.set_value(options[0])
            values_changed()

        def preset_changed():
            self.set_industry_presets(self.preset_combo.input.currentData())
            values_changed()

        self.preset_combo.changed.connect(preset_changed)

        dependency = SumDependency(100)
        for branche in self.branchen:
            feature = self.gewerbeanteile.get(id_branche=branche.id,
                                              id_teilflaeche=self.area.id)
            value = feature.anteil_definition if feature else 0
            slider = Slider(maximum=100, width=200, lockable=True)
            param = Param(
                value, slider, label=f'{branche.Name_Branche_ProjektCheck}',
                unit='%'
            )
            slider.changed.connect(slider_changed)
            dependency.add(param)
            self.params.add(param, name=branche.param_gewerbenutzung)

        self.params.add(Seperator())

        self.params.add(Title('Voraussichtliche Anzahl an Arbeitsplätzen'))

        self.auto_check = Checkbox()
        self.params.auto_check = Param(
            bool(self.area.ap_ist_geschaetzt), self.auto_check,
            label='Automatische Schätzung'
        )

        self.ap_slider = Slider(maximum=10000)
        self.params.arbeitsplaetze_insgesamt = Param(
            self.area.ap_gesamt, self.ap_slider,
            label='Zahl der Arbeitsplätze\n'
            'nach Vollbezug (Summe über alle Branchen)'
        )

        def toggle_auto_check():
            # disable input for manual setting of jobs
            # when auto check is enabled
            read_only = self.auto_check.value
            for _input in [self.ap_slider.slider, self.ap_slider.spinbox]:
                _input.setAttribute(Qt.WA_TransparentForMouseEvents, read_only)
                _input.setFocusPolicy(Qt.NoFocus if read_only
                                      else Qt.StrongFocus)
                _input.update()
            values_changed()

        self.auto_check.changed.connect(toggle_auto_check)
        toggle_auto_check()

        # set to default preset if assignment is new
        if len(self.gewerbeanteile) == 0:
            self.set_industry_presets(self.DEFAULT_INDUSTRY_ID)

        self.params.changed.connect(self.save)
        self.params.show(
            title='Gewerbe: Bezugszeitraum und Maß der baulichen Nutzung')

    def save(self):
        for branche in self.branchen:
            feature = self.gewerbeanteile.get(id_branche=branche.id,
                                              id_teilflaeche=self.area.id)
            if not feature:
                feature = self.gewerbeanteile.add(
                    id_branche=branche.id, id_teilflaeche=self.area.id)
            feature.anteil_definition = getattr(
                self.params, branche.param_gewerbenutzung).value
            feature.name_branche = branche.Name_Branche_ProjektCheck
            feature.anzahl_jobs_schaetzung = getattr(
                branche, 'estimated_jobs', 0)
            feature.dichtekennwert = getattr(
                branche, 'jobs_per_ha', 0)
            feature.save()

        self.area.beginn_nutzung = self.params.beginn_nutzung.value
        self.area.aufsiedlungsdauer = self.params.aufsiedlungsdauer.value
        self.area.ap_gesamt = self.params.arbeitsplaetze_insgesamt.value
        self.area.ap_ist_geschaetzt = self.params.auto_check.value

        self.area.save()

        # just estimate for output in case auto estimation is deactivated
        # (estimated values needed in any case)
        self.estimate_jobs()
        self.set_growth(self.area)
        self.set_percentages(self.area)
        self.set_ways(self.area)

        Traffic.reset()

    def clear(self, area):
        self.gewerbeanteile.filter(id_teilflaeche=area.id).delete()
        self.ap_nach_jahr.filter(id_teilflaeche=area.id).delete()
        area.ap_gesamt = None
        area.save()

    def set_growth(self, area):

        n_jobs = area.ap_gesamt
        begin = area.beginn_nutzung
        duration = area.aufsiedlungsdauer

        end = begin + self.BETRACHTUNGSZEITRAUM_JAHRE - 1

        self.ap_nach_jahr.filter(id_teilflaeche=area.id).delete()

        for progress in range(0, end - begin + 1):
            proc_factor = (float(progress + 1) / duration
                           if progress + 1 <= duration
                           else 1)
            year = begin + progress

            self.ap_nach_jahr.add(
                id_teilflaeche=self.area.id, jahr=year,
                arbeitsplaetze=n_jobs * proc_factor
            )

    def set_percentages(self, area):
        '''this already could have done when saving,
        but is here based on the old code'''
        df = self.gewerbeanteile.filter(id_teilflaeche=area.id).to_pandas()
        df['anteil_branche'] = df['anteil_definition'] * df['dichtekennwert']
        df['anteil_branche'] /= df['anteil_branche'].sum()
        self.gewerbeanteile.update_pandas(df)

    def set_ways(self, area):
        df_anteile = self.gewerbeanteile.filter(
            id_teilflaeche=area.id).to_pandas()
        df_basedata = (self.basedata.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt').features().filter(
                ID_Branche_ProjektCheck__gt=0).to_pandas())
        df_basedata.rename(columns={'ID_Branche_ProjektCheck': 'id_branche'},
                           inplace=True)
        estimated = df_anteile['anzahl_jobs_schaetzung']
        estimated_sum = estimated.sum()
        preset = area.ap_gesamt
        cor_factor = preset / estimated_sum if estimated_sum > 0 else 0
        joined = df_anteile.merge(df_basedata, on='id_branche', how='left')
        n_ways = estimated * cor_factor * joined['Wege_je_Beschäftigten']
        n_ways_miv = n_ways * joined['Anteil_Pkw_Fahrer'] / 100

        area.wege_gesamt = int(n_ways.sum())
        area.wege_miv = int(n_ways_miv.sum())

        area.save()

    def close(self):
        if hasattr(self, 'params'):
            self.params.close()


class Einzelhandel:
    def __init__(self, basedata, layout):
        self.basedata = basedata
        self.sortimente_base = basedata.get_table(
            'Einzelhandel_Sortimente', 'Definition_Projekt'
        )
        self.verkaufsflaechen = Verkaufsflaechen.features(create=True)
        self.layout = layout

    def setup_params(self, area):
        self.area = area
        clear_layout(self.layout)
        self.params = Params(self.layout,
                             help_file='definitionen_einzelhandel.txt')

        self.params.add(Title('Verkaufsfläche'))

        for sortiment in self.sortimente_base.features():
            feature = self.verkaufsflaechen.get(id_sortiment=sortiment.id,
                                                id_teilflaeche=self.area.id)
            value = feature.verkaufsflaeche_qm if feature else 0
            self.params.add(Param(
                value,
                Slider(maximum=20000),
                label=f'{sortiment.Name_Sortiment_ProjektCheck}', unit='m²'),
                name=sortiment.param_vfl
            )
        self.params.changed.connect(self.save)
        self.params.show(
            title='Einzelhandel: Bezugszeitraum und Maß der baulichen Nutzung')

    def save(self):
        vkfl_sum = 0
        for sortiment in self.sortimente_base.features():
            feature = self.verkaufsflaechen.get(id_sortiment=sortiment.id,
                                                id_teilflaeche=self.area.id)
            if not feature:
                feature = self.verkaufsflaechen.add(
                    id_sortiment=sortiment.id, id_teilflaeche=self.area.id)
            vkfl = getattr(self.params, sortiment.param_vfl).value
            feature.verkaufsflaeche_qm = vkfl
            vkfl_sum += vkfl
            feature.name_sortiment = sortiment.Name_Sortiment_ProjektCheck
            feature.save()

        self.area.vf_gesamt = vkfl_sum
        self.area.save()

        # ToDo: create market if verkaufsflaeche lebensmittel
        #self.create_market()
        self.set_ways(self.area)

        Traffic.reset()

    def clear(self, area):
        self.verkaufsflaechen.filter(id_teilflaeche=area.id).delete()
        area.vf_gesamt = None
        area.save()

    def create_market(self):
        raise NotImplementedError

    def set_ways(self, area):
        df_verkaufsflaechen = self.verkaufsflaechen.filter(
            id_teilflaeche=area.id).to_pandas()
        default_branche = self.basedata.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt').features().get(
                ID_Branche_ProjektCheck=0)
        df_sortimente = self.sortimente_base.to_pandas()
        df_sortimente.rename(
            columns={'ID_Sortiment_ProjektCheck': 'id_sortiment'}, inplace=True)

        joined = df_verkaufsflaechen.merge(df_sortimente, on='id_sortiment',
                                           how='left')

        n_ways = (joined['verkaufsflaeche_qm'] *
                  joined['Besucher_je_qm_Vfl'] *
                  joined['Wege_je_Besucher'])
        n_ways_miv = n_ways * joined['Anteil_Pkw_Fahrer'] / 100

        n_job_ways = (joined['verkaufsflaeche_qm'] *
                      joined['AP_je_qm_Vfl'] *
                      default_branche.Wege_je_Beschäftigten)
        n_job_miv = n_job_ways * default_branche.Anteil_Pkw_Fahrer / 100

        area.wege_gesamt = int(n_ways.sum() + n_job_ways.sum())
        area.wege_miv = int(n_ways_miv.sum() + n_job_miv.sum())

        area.save()

    def close(self):
        if hasattr(self, 'params'):
            self.params.close()


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projektdefinition'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'
    layer_group = 'Projektdefinition'

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(
            lambda: self.change_area())

        self.connector_setter = TrafficConnectors(
            self.ui, self.canvas, self.project)
        type_layout = self.ui.type_parameter_group.layout()
        # ToDo: somehow generate this (resp. assign index) from the enum
        #  preferably store labels and id in a base table
        self.types = [
            ('Nutzung noch nicht definiert', None),
            ('Wohnen', Wohnen(self.basedata, type_layout)),
            ('Gewerbe', Gewerbe(self.basedata, type_layout)),
            ('Einzelhandel', Einzelhandel(self.basedata, type_layout))
        ]
        self.typ = None

        pdf_path = os.path.join(
            self.settings.HELP_PATH, 'Anleitung_Projektdefinition.pdf')
        self.ui.manual_button.clicked.connect(lambda: open_file(pdf_path))

    def load_content(self):
        super().load_content()
        self.areas = Teilflaechen.features()
        self.connectors = Connectors.features()
        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        for area in self.areas:
            tou_label = self.types[area.nutzungsart][0]
            self.ui.area_combo.addItem(f'{area.name} ({tou_label})', area)
        self.ui.area_combo.blockSignals(False)
        self.show_outputs()
        self.change_area()

    def change_area(self):

        self.area = self.ui.area_combo.itemData(
            self.ui.area_combo.currentIndex())

        layer = self.tou_output.layer
        if layer:
            layer.removeSelection()
            layer.select(self.area.id)

        self.connector_setter.load_content(self.area)

        self.setup_type()
        self.setup_type_params()

    def show_outputs(self, zoom=False):
        table = Teilflaechen.get_table()
        self.tou_output = ProjectLayer.from_table(
            table, groupname=self.layer_group)
        self.tou_output.draw(label='Nutzungen des Plangebiets',
                            style_file='definitions.qml', redraw=False)
        if zoom:
            self.tou_output.zoom_to()
        output = ProjectLayer.from_table(table, groupname='Hintergrund',
                                         prepend=False)
        output.draw(label='Umriss des Plangebiets', style_file='areas.qml')
        self.connector_setter.show_connectors()

    def setup_type(self):
        layout = self.ui.parameter_group.layout()
        clear_layout(layout)
        self.params = Params(layout,
                             help_file='definitionen_flaechen.txt', )
        self.params.name = Param(self.area.name, LineEdit(width=300),
                                 label='Name')

        self.params.add(Seperator(margin=0))

        ha = round(self.area.geom.area()) / 10000
        self.area.area = ha
        self.params.area = Param(ha, label='Größe', unit='ha')

        self.params.typ = Param(
            self.types[self.area.nutzungsart][0],
            ComboBox([t[0] for t in self.types], width=300),
            label='Nutzungsart'
        )

        def type_changed():
            name = self.params.name.value
            type_labels = [t[0] for t in self.types]
            tou_id = type_labels.index(self.params.typ.value)
            self.area.nutzungsart = tou_id
            tou_label = self.types[tou_id][0]
            self.ui.area_combo.setItemText(
                self.ui.area_combo.currentIndex(),
                f'{name} ({tou_label})'
            )
            self.area.name = name
            self.area.save()
            # update connector names
            connector = self.connectors.get(id_teilflaeche=self.area.id)
            connector.name_teilflaeche = self.area.name
            connector.save()
            if self.typ:
                self.typ.clear(self.area)
            self.setup_type_params()
            self.canvas.refreshAllLayers()
            Traffic.reset()
        self.params.changed.connect(type_changed)
        self.params.show(title='Teilfläche definieren')

    def setup_type_params(self):
        tou_label = self.types[self.area.nutzungsart][0]
        title = f'Maß der baulichen Nutzung ({tou_label})'
        self.ui.type_parameter_group.setTitle(title)

        clear_layout(self.ui.type_parameter_group.layout())
        if self.typ:
            self.typ.close()
        self.typ = self.types[self.area.nutzungsart][1]
        if self.typ is None:
            self.ui.type_parameter_group.setVisible(False)
            return
        self.ui.type_parameter_group.setVisible(True)
        self.typ.setup_params(self.area)
        self.typ.params.changed.connect(lambda: self.canvas.refreshAllLayers())

    def close(self):
        self.connector_setter.close()
        layer = self.tou_output.layer
        if layer:
            layer.removeSelection()
        if hasattr(self, 'params'):
            self.params.close()
        if self.typ:
            self.typ.close()
        super().close()
