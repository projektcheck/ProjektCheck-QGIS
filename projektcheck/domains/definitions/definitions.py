from projektcheck.base import (Domain, Params, Param, SpinBox, ComboBox,
                               Title, Seperator, LineEdit, Geopackage, Field,
                               Slider, DoubleSpinBox, SumDependency, Checkbox)
from projektcheck.utils.utils import clearLayout
from projektcheck.domains.constants import Nutzungsart
from projektcheck.domains.definitions.tables import (
    Teilflaechen, Verkaufsflaechen, Wohneinheiten,
    WohnenStruktur, Gewerbeanteile, Projektrahmendaten)
from projektcheck.domains.jobs_inhabitants.tables import (
    ApProJahr, Branchenanteile)


class Wohnen:
    def __init__(self, basedata, layout):
        self.gebaeudetypen = basedata.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        )
        self.wohneinheiten = Wohneinheiten.features(create=True)
        self.layout = layout

    def setup_params(self, area):
        self.area = area
        clearLayout(self.layout)
        self.params = Params(self.layout)
        self.params.add(Title('Bezugszeitraum'))
        #params.begin = Param(0, Slider(minimum=2000, maximum=2100),
                                  #label='Beginn des Bezuges')
        self.params.begin = Param(
            2000, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges'
        )
        self.params.period = Param(1, SpinBox(minimum=1, maximum=100),
                                        label='Dauer des Bezuges')
        self.params.add(Seperator())

        self.params.add(Title('Anzahl Wohneinheiten nach Gebäudetypen'))

        for bt in self.gebaeudetypen.features():
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

        for bt in self.gebaeudetypen.features():
            param_name = bt.param_ew_je_we
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            value = feature.ew_je_we if feature else 0
            self.params.add(Param(
                value,
                DoubleSpinBox(step=0.1, maximum=50),
                label=f'... in {bt.display_name}'),
                name=param_name
            )
        self.params.changed.connect(self.save)
        self.params.show()

    def save(self):
        for bt in self.gebaeudetypen.features():
            feature = self.wohneinheiten.get(id_gebaeudetyp=bt.id,
                                             id_teilflaeche=self.area.id)
            if not feature:
                feature = self.wohneinheiten.add(
                    id_gebaeudetyp=bt.id, id_teilflaeche=self.area.id)
            feature.we = getattr(self.params, bt.param_we).value
            feature.ew_je_we = getattr(self.params, bt.param_ew_je_we).value
            feature.name_gebaeudetyp = bt.NameGebaeudetyp
            feature.save()

    def clear(self, area):
        self.wohneinheiten.filter(id_teilflaeche=area.id).delete()


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

        self.branchen = list(self.basedata.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt'
        ).features())

        presets = self.basedata.get_table(
            'Vorschlagswerte_Branchenstruktur', 'Definition_Projekt'
        )
        self.df_presets = presets.to_pandas()

        density = self.basedata.get_table(
            'Dichtekennwerte_Gewerbe', 'Definition_Projekt'
        )
        self.df_density = density.to_pandas()

        industry_types = self.basedata.get_table(
            'Gewerbegebietstypen', 'Definition_Projekt'
        )
        self.df_industry_types = industry_types.to_pandas()

        default_idx = self.df_industry_types['IDGewerbegebietstyp'] == \
            self.DEFAULT_INDUSTRY_ID
        self.df_industry_types.loc[
            default_idx, 'Name_Gewerbegebietstyp'] += ' (default)'

    def set_industry_presets(self, preset_id):
        """set all branche values to db-presets of given gewerbe-id"""
        if preset_id == -1:
            return
        idx = self.df_presets['IDGewerbegebietstyp'] == preset_id
        presets = self.df_presets[idx]
        for branche in self.branchen:
            param = getattr(self.params, branche.param_gewerbenutzung)
            p_idx = presets['ID_Branche_ProjektCheck'] == branche.id
            preset = int(presets[p_idx]['Vorschlagswert_in_Prozent'].values[0])
            param.value = preset

    def estimate_jobs(self):
        """calculate estimation of number of jobs
        sets estimated jobs to branchen"""
        gemeindetyp = self.area.gemeinde_typ
        df_kennwerte = self.df_density[
            self.df_density['Gemeindetyp_ProjektCheck'] == gemeindetyp]

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
        self.params.begin_nutzung = Param(
            area.begin_nutzung, SpinBox(minimum=2000, maximum=2100),
            label='Beginn des Bezuges'
        )
        self.params.aufsiedlungsdauer = Param(
            area.aufsiedlungsdauer, SpinBox(minimum=1, maximum=100),
            label='Dauer des Bezuges (Jahre, 1 = Bezug wird noch\n'
            'im Jahr des Bezugsbeginns abgeschlossen)'
        )

        self.params.add(
            Title('Voraussichtlicher Anteil der Branchen an der Nettofläche'))

        self.params.add(Seperator())

        preset_names = self.df_industry_types['Name_Gewerbegebietstyp'].values
        preset_ids = self.df_industry_types['IDGewerbegebietstyp'].values
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

        self.area.begin_nutzung = self.params.begin_nutzung.value
        self.area.aufsiedlungsdauer = self.params.aufsiedlungsdauer.value
        self.area.ap_gesamt = self.params.arbeitsplaetze_insgesamt.value
        self.area.ap_ist_geschaetzt = self.params.auto_check.value

        # just estimate for output in case auto estimation is deactivated
        # (estimated values needed in any case)
        self.estimate_jobs()
        self.calculate_growth(self.area)
        self.calculate_percentages(self.area)
        self.calculate_ways(self.area)

    def clear(self, area):
        self.gewerbeanteile.filter(id_teilflaeche=area.id).delete()
        self.ap_nach_jahr.filter(id_teilflaeche=area.id).delete()
        self.ap_nach_jahr.filter(id_teilflaeche=area.id).delete()

    def calculate_growth(self, area): ### Structure and age ###
        #flaechen_table = 'Teilflaechen_Plangebiet'
        #project_table = 'Projektrahmendaten'
        #jobs_year_table = 'AP_nach_Jahr'
        #results_workspace = 'FGDB_Bewohner_Arbeitsplaetze.gdb'

        n_jobs = self.params.arbeitsplaetze_insgesamt.value
        begin = self.params.begin_nutzung.value
        duration = self.params.aufsiedlungsdauer.value

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

    def calculate_percentages(self, area):
        '''this already could have done when saving,
        but is here based on the old code'''
        df = self.gewerbeanteile.filter(id_teilflaeche=area.id).to_pandas()
        df['anteil_branche'] = df['anteil_definition'] * df['dichtekennwert']
        df['anteil_branche'] /= df['anteil_branche'].sum()
        self.gewerbeanteile.update_pandas(df)

    def calculate_ways(self, area):
        df_anteile = self.gewerbeanteile.filter(
            id_teilflaeche=area.id).to_pandas()
        df_basedata = (self.basedata.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt').to_pandas())
        df_basedata.rename(columns={'ID_Branche_ProjektCheck': 'id_branche'},
                           inplace=True)
        estimated = df['anzahl_jobs_schaetzung']
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
        self.sortimente = basedata.get_table(
            'Einzelhandel_Sortimente', 'Definition_Projekt'
        )
        self.verkaufsflaechen = Verkaufsflaechen.features(create=True)
        self.layout = layout

    def setup_params(self, area):
        self.area = area
        clearLayout(self.layout)
        self.params = Params(self.layout)

        for sortiment in self.sortimente.features():
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
        for sortiment in self.sortimente.features():
            feature = self.verkaufsflaechen.get(id_sortiment=sortiment.id,
                                                id_teilflaeche=self.area.id)
            if not feature:
                feature = self.verkaufsflaechen.add(
                    id_sortiment=sortiment.id, id_teilflaeche=self.area.id)
            feature.verkaufsflaeche_qm = getattr(
                self.params, sortiment.param_vfl).value
            feature.name_sortiment = sortiment.Name_Sortiment_ProjektCheck
            feature.save()

    def clear(self, area):
        self.verkaufsflaechen.filter(id_teilflaeche=area.id).delete()


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
        self.params.name = Param(self.area.name, LineEdit(), label='Name')
        ha = round(self.area.geom.area()) / 10000
        self.area.area = ha
        self.params.area = Param(ha, label='Größe', unit='ha')
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
