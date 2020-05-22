# -*- coding: utf-8 -*-
from projektchecktools.domains.definitions.tables import (Teilflaechen,
                                                          Projektrahmendaten)
from projektchecktools.domains.municipaltaxrevenue.tables import (
    Gemeindebilanzen, GrundsteuerSettings)
from projektchecktools.domains.definitions.tables import Wohneinheiten
from projektchecktools.base.domain import Worker


class GrundsteuerCalculation(Worker):
    _param_projectname = 'projectname'
    rings = [1500, 2500, 3500, 4500, 6500, 8500, 11500, 14500, 18500, 25000]

    # ToDo: that is not a good way to allocate the fields to the building type
    geb_types_suffix = {
        1: 'EFH',
        2: 'DHH',
        3: 'RHW',
        4: 'MFH'
    }

    def __init__(self, project, typ='Einwohner', parent=None):
        super().__init__(parent=parent)
        self.typ = typ
        self.project = project
        self.bilanzen = Gemeindebilanzen.features(project=project)
        self.grst_settings = GrundsteuerSettings.features(project=project)[0]
        self.project_frame = Projektrahmendaten.features(
            project=self.project)[0]
        self.messzahlen = self.project.basedata.get_table(
            'GrSt_Wohnflaeche_und_Steuermesszahlen', 'Einnahmen').features()

    def work(self):
        self.log('Berechne Grundsteuer...')
        messbetrag_wohnen = self.calc_messbetrag_wohnen(
            self.grst_settings.is_new_bundesland)
        messbetrag_gewerbe = self.calc_messbetrag_gewerbe()
        gem = self.bilanzen.get(AGS=self.project_frame.ags)
        gst = (messbetrag_wohnen + messbetrag_gewerbe) * gem.Hebesatz_GewSt
        gem.grundsteuer = gst
        gem.save()

    def calc_messbetrag_wohnen(self, is_new_bundesland):
        vvf = self.project.basedata.get_table(
            'GrSt_Vervielfaeltiger', 'Einnahmen').features()
        gem_gkl = self.project.basedata.get_table(
            'bkg_gemeinden', 'Basisdaten_deutschland').features().get(
                AGS=self.project_frame.ags).GemGroessKlass64
        we = Wohneinheiten.features()

        messbetrag_sum = 0

        for m_gt in self.messzahlen:
            geb_typ_id = m_gt.IDGebaeudetyp
            wohnfl = m_gt.Mittlere_Wohnflaeche
            aufschlag = m_gt.Aufschlag_Garagen_Carport
            fn = f'{self.geb_types_suffix[geb_typ_id]}_Rohmiete'
            rohmiete = self.grst_settings[fn] / 100 if not is_new_bundesland \
                else 0.46
            # special case for EFH and new bundesland
            if geb_typ_id == 1 and is_new_bundesland:
                rohmiete = (24 / 1.95583 * m_gt.Umbauter_Raum_m3 +
                            550 + self.grst_settings.qm_Grundstueck_pro_WE_EFH *
                            self.grst_settings.Bodenwert_SWV / 100)
            vervielf = vvf.get(Gemeindegroessenklasse64=gem_gkl,
                               IDGebaeudetyp=geb_typ_id).Vervielfaeltiger
            ewert = (12 * wohnfl * rohmiete + aufschlag) * vervielf
            anzahl_we = sum(we.filter(id_gebaeudetyp=geb_typ_id).values('we'))
            betrag = anzahl_we * (
                min(38346, ewert) * m_gt.Steuermesszahl_bis_38346_EUR +
                max(0, ewert-38346) * m_gt.Steuermesszahl_ab_38346_EUR
            )
            messbetrag_sum += betrag
        return messbetrag_sum

    def calc_messbetrag_gewerbe(self):
        ewert = (1685 * self.grst_settings.Bueroflaeche +
                 800 * self.grst_settings.Verkaufsraeume) * 0.1554
        return ewert * 0.0035