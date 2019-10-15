import pandas as pd
from projektcheck.base import (Domain, Params, Param, SpinBox, ComboBox,
                               Title, Seperator, LineEdit, Geopackage, Field,
                               Slider, DoubleSpinBox, SumDependency, Checkbox)
from projektcheck.utils.utils import clearLayout
from projektcheck.domains.constants import Nutzungsart
from projektcheck.domains.definitions.tables import (
    Teilflaechen, Verkaufsflaechen, Wohneinheiten,
    Gewerbeanteile, Projektrahmendaten)
from projektcheck.domains.jobs_inhabitants.tables import (
    ApProJahr, Branchenanteile, WohnenProJahr, WohnenStruktur)


class Wohnen:
    BETRACHTUNGSZEITRAUM_JAHRE = 25

    def __init__(self, basedata, layout):
        self.gebaeudetypen_base = basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        )
        self.einwohner_base = basedata.get_table(
            'Einwohner_pro_WE', 'Bewohner_Arbeitsplaetze'
        )
        self.wohneinheiten = Wohneinheiten.features(create=True)
        self.wohnen_struktur = WohnenStruktur.features(create=True)
        self.wohnen_pro_jahr = WohnenProJahr.features(create=True)
        self.layout = layout

    def setup_params(self, area):
        self.area = area
        clearLayout(self.layout)
        self.params = Params(self.layout)
        self.params.add(Title('Bezugszeitraum'))
        self.params.beginn_nutzung = Param(
            area.beginn_nutzung, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges'
        )
        self.params.aufsiedlungsdauer = Param(
            area.aufsiedlungsdauer, SpinBox(minimum=1, maximum=100),
            label='Dauer des Bezuges')
        self.params.add(Seperator())

        self.params.add(Title('Anzahl Wohneinheiten nach Gebäudetypen'))

        for bt in self.gebaeudetypen_base.features():
            param_name = bt.param_we
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            value = feature.we if feature else 0
            self.params.add(Param(
                value, Slider(maximum=500),
                label=f'... in {bt.display_name}'),
                name=param_name
            )
        self.params.add(Seperator())

        self.params.add(Title('Mittlere Anzahl Einwohner pro Wohneinheit\n'
                              '(3 Jahre nach Bezug)'))

        for bt in self.gebaeudetypen_base.features():
            param_name = bt.param_ew_je_we
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            # set to default if no feature yet
            value = feature.ew_je_we if feature else bt.default_ew_je_we
            self.params.add(Param(
                value,
                DoubleSpinBox(step=0.1, maximum=50),
                label=f'... in {bt.display_name}'),
                name=param_name
            )

        self.params.changed.connect(self.save)
        self.params.show()

    def save(self):
        we_sum = 0
        for bt in self.gebaeudetypen_base.features():
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
            cor_factor = ew_je_we / bt.Ew_pro_WE_Referenz
            feature.korrekturfaktor = cor_factor
            feature.name_gebaeudetyp = bt.NameGebaeudetyp
            feature.save()

        self.area.beginn_nutzung = self.params.beginn_nutzung.value
        self.area.aufsiedlungsdauer = self.params.aufsiedlungsdauer.value
        self.area.we_gesamt = we_sum

        self.area.save()

        self.set_development(self.area)
        self.set_ways(self.area)

    def set_development(self, area):
        begin = area.beginn_nutzung
        duration = area.aufsiedlungsdauer
        end = begin + self.BETRACHTUNGSZEITRAUM_JAHRE - 1

        df_einwohner_base = self.einwohner_base.to_pandas()
        df_wohneinheiten_tfl = self.wohneinheiten.filter(
            id_teilflaeche=area.id).to_pandas()

        wohnen_struktur_tfl = self.wohnen_struktur.filter(
            id_teilflaeche=area.id)
        wohnen_struktur_tfl.delete()
        wohnen_pro_jahr_tfl = self.wohnen_pro_jahr.filter(
            id_teilflaeche=area.id)
        wohnen_pro_jahr_tfl.delete()

        df_wohnen_struktur = wohnen_struktur_tfl.to_pandas()

        flaechen_template = pd.DataFrame()
        geb_types = df_wohneinheiten_tfl['id_gebaeudetyp'].values
        flaechen_template['id_gebaeudetyp'] = geb_types
        flaechen_template['id_teilflaeche'] = area.id
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
            entry['id_teilflaeche'] = area.id
            df_wohnen_pro_jahr = df_wohnen_pro_jahr.append(entry)

        self.wohnen_pro_jahr.update_pandas(df_wohnen_pro_jahr)

    def set_ways(self, area):
        df_wohneinheiten = self.wohneinheiten.filter(
            id_teilflaeche=area.id).to_pandas()
        df_gebaeudetypen = self.gebaeudetypen_base.to_pandas()
        df_gebaeudetypen.rename(columns={'IDGebaeudetyp': 'id_gebaeudetyp'},
                                inplace=True)
        joined = df_wohneinheiten.merge(df_gebaeudetypen, on='id_gebaeudetyp')

        n_ew = joined['ew_je_we'] * joined['we']
        n_ways = n_ew * joined['Wege_je_Einwohner']
        n_ways_miv = n_ways * joined['Anteil_Pkw_Fahrer'] / 100

        area.wege_gesamt = int(n_ways.sum())
        area.wege_miv = int(n_ways_miv.sum())

        area.save()

    def clear(self, area):
        self.wohneinheiten.filter(id_teilflaeche=area.id).delete()
        area.we_gesamt = None
        area.save()


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
        clearLayout(self.layout)
        self.params = Params(self.layout)

        self.params.add(Title('Bezugszeitraum'))
        self.params.beginn_nutzung = Param(
            area.beginn_nutzung, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges'
        )
        self.params.aufsiedlungsdauer = Param(
            area.aufsiedlungsdauer, SpinBox(minimum=1, maximum=100),
            label='Dauer des Bezuges (Jahre, 1 = Bezug wird noch\n'
            'im Jahr des Bezugsbeginns abgeschlossen)'
        )

        self.params.add(Seperator(margin=10))

        self.params.add(
            Title('Voraussichtlicher Anteil der Branchen an der Nettofläche'))

        preset_names = self.df_industry_types_base['Name_Gewerbegebietstyp'].values
        preset_ids = self.df_industry_types_base['IDGewerbegebietstyp'].values
        self.preset_combo = ComboBox(
            ['Benutzerdefiniert'] + list(preset_names), [-1] + list(preset_ids))

        self.i = 0

        def values_changed():
            if self.auto_check.value:
                n_jobs = self.estimate_jobs()
                self.ap_slider.set_value(n_jobs)

        def slider_changed():
            self.preset_combo.set_value('Benutzerdefiniert')
            values_changed()

        def preset_changed():
            self.set_industry_presets(self.preset_combo.input.currentData())
            values_changed()

        self.params.add(self.preset_combo)
        self.preset_combo.changed.connect(preset_changed)

        dependency = SumDependency(100)
        for branche in self.branchen:
            param_name = branche.param_gewerbenutzung
            feature = self.gewerbeanteile.get(id_branche=branche.id,
                                              id_teilflaeche=self.area.id)
            value = feature.anteil_definition if feature else 0
            slider = Slider(maximum=100, width=200)
            param = Param(
                value,  slider, label=f'{branche.Name_Branche_ProjektCheck}',
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
            enabled = not self.auto_check.value
            for _input in [self.ap_slider.slider, self.ap_slider.spinbox]:
                _input.setEnabled(enabled)
                _input.update()
            values_changed()

        self.auto_check.changed.connect(toggle_auto_check)
        toggle_auto_check()

        ## set to default preset if assignment is new
        #if len(self.gewerbeanteile) == 0:
            #self.set_industry_presets(self.DEFAULT_INDUSTRY_ID)

        self.params.changed.connect(self.save)
        self.params.show()

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
        n_ways_miv = estimated * cor_factor * joined['Anteil_Pkw_Fahrer'] / 100

        area.wege_gesamt = int(n_ways.sum())
        area.wege_miv = int(n_ways_miv.sum())

        area.save()


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
        clearLayout(self.layout)
        self.params = Params(self.layout)

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
        self.params.show()

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

        # ToDo: wege arbeitsplaetze?
        n_jobs = joined['AP_je_qm_Vfl'] * joined['verkaufsflaeche_qm']
        n_job_ways = (joined['verkaufsflaeche_qm'] *
                      joined['AP_je_qm_Vfl'] *
                      default_branche.Wege_je_Beschäftigten)
        n_job_miv = n_job_ways * default_branche.Anteil_Pkw_Fahrer / 100

        area.wege_gesamt = int(n_ways.sum() + n_job_ways.sum())
        area.wege_miv = int(n_ways_miv.sum() + n_job_miv.sum())

        area.save()


class ProjectDefinitions(Domain):
    """"""
    ui_label = 'Projekt-Definitionen'
    ui_file = 'ProjektCheck_dockwidget_definitions.ui'

    def setupUi(self):
        self.ui.area_combo.currentIndexChanged.connect(self.change_area)
        self.areas = Teilflaechen.features()
        self.ui.area_combo.blockSignals(True)
        self.ui.area_combo.clear()
        for area in self.areas:
            self.ui.area_combo.addItem(area.name, area.id)
        self.ui.area_combo.blockSignals(False)

        type_layout = self.ui.type_parameter_group.layout()
        self.types = {
            'Undefiniert': None,
            'Wohnen': Wohnen(self.basedata, type_layout),
            'Gewerbe': Gewerbe(self.basedata, type_layout),
            'Einzelhandel': Einzelhandel(self.basedata, type_layout)
        }
        self.typ = None
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
        self.params.name = Param(self.area.name, LineEdit(width=300),
                                 label='Name')

        self.params.add(Seperator(margin=0))

        ha = round(self.area.geom.area()) / 10000
        self.area.area = ha
        self.params.area = Param(ha, label='Größe', unit='ha')
        type_names = [n.capitalize() for n in Nutzungsart._member_names_]

        self.params.typ = Param(
            Nutzungsart(self.area.nutzungsart).name.capitalize(),
            ComboBox(type_names, width=300),
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
            if self.typ:
                self.typ.clear(self.area)
            self.setup_type_params()
            self.canvas.refreshAllLayers()
        self.params.changed.connect(type_changed)

    def setup_type_params(self):
        typ = self.params.typ.value
        clearLayout(self.ui.type_parameter_group.layout())
        self.typ = self.types[typ]
        if self.typ is None:
            return
        self.typ.setup_params(self.area)
        self.typ.params.changed.connect(lambda: self.canvas.refreshAllLayers())

    def close(self):
        # ToDo: implement this in project (collecting all used workscpaces)
        if hasattr(self, 'areas'):
            self.areas._table.workspace.close()
        super().close()
