# -*- coding: utf-8 -*-
'''
***************************************************************************
    tax.py
    ---------------------
    Date                 : May 2020
    Copyright            : (C) 2020 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

calculation of taxes
'''

__author__ = 'Christoph Franke'
__date__ = '22/05/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

from projektcheck.domains.definitions.tables import (
    Teilflaechen, Projektrahmendaten, Gewerbeanteile, Verkaufsflaechen)
from projektcheck.domains.municipaltaxrevenue.tables import (
    Gemeindebilanzen, GrundsteuerSettings, EinwohnerWanderung,
    BeschaeftigtenWanderung)
from projektcheck.domains.constants import Nutzungsart
from projektcheck.domains.definitions.tables import Wohneinheiten
from projektcheck.base.domain import Worker


class GrundsteuerCalculation(Worker):
    '''
    calculation of property tax
    '''

    # ToDo: that is not a good way to allocate the fields to the building type
    geb_types_suffix = {
        1: 'EFH',
        2: 'DHH',
        3: 'RHW',
        4: 'MFH'
    }

    def __init__(self, project, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.project = project
        self.bilanzen = Gemeindebilanzen.features(project=project)
        self.grst_settings = GrundsteuerSettings.features(project=project)[0]
        self.project_frame = Projektrahmendaten.features(project=project)[0]

    def work(self):
        self.log('Berechne Grundsteuer...')
        messbetrag_wohnen = self.calc_messbetrag_wohnen(
            self.grst_settings.is_new_bundesland)
        messbetrag_gewerbe = self.calc_messbetrag_gewerbe()
        for gem in self.bilanzen:
            if gem.AGS == self.project_frame.ags:
                gst = ((messbetrag_wohnen + messbetrag_gewerbe) *
                       self.grst_settings.Hebesatz_GrStB / 100)
                rnd = 1000 if gst >= 500 else 100
                gst = round(gst/rnd) * rnd
            else:
                gst = 0
            gem.grundsteuer = gst
            gem.save()
        return True

    def calc_messbetrag_wohnen(self, is_new_bl):
        '''
        base rate for living

        Parameters
        ----------
        is_new_bl : bool
            project area is part of "Neue Bundesländer" if True (different base
            calculations)
        '''
        messzahlen = self.project.basedata.get_table(
            'GrSt_Wohnflaeche_und_Steuermesszahlen', 'Einnahmen').features()
        vvf = self.project.basedata.get_table(
            'GrSt_Vervielfaeltiger', 'Einnahmen').features()
        gem_gkl = self.project.basedata.get_table(
            'bkg_gemeinden', 'Basisdaten_deutschland').features().get(
                AGS=self.project_frame.ags).GemGroessKlass64
        we = Wohneinheiten.features()

        messbetrag_sum = 0

        for m_gt in messzahlen:
            geb_typ_id = m_gt.IDGebaeudetyp
            # special case for EFH and new bundesland
            if geb_typ_id == 1 and is_new_bl:
                ewert = (24 / 1.95583 * m_gt.Umbauter_Raum_m3 +
                        550 + self.grst_settings.qm_Grundstueck_pro_WE_EFH *
                        self.grst_settings.Bodenwert_SWV / 100)
            else:
                wohnfl = m_gt.Mittlere_Wohnflaeche
                aufschlag = m_gt.Aufschlag_Garagen_Carport
                fn = f'{self.geb_types_suffix[geb_typ_id]}_Rohmiete'
                rohmiete = self.grst_settings[fn] / 100 if not is_new_bl \
                    else 0.46
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
        '''
        base rate for business taxes
        '''
        ewert = (1685 * self.grst_settings.Bueroflaeche +
                 800 * self.grst_settings.Verkaufsraeume) * 0.1554
        return ewert * 0.0035


class EinkommensteuerCalculation(Worker):
    '''
    calculation of income tax
    '''
    def __init__(self, project, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.project = project
        self.bilanzen = Gemeindebilanzen.features(project=project)
        self.wanderung = EinwohnerWanderung.features(project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.we = Wohneinheiten.features()

    def work(self):
        self.log('Berechne Einkommensteuer...')
        est_pro_wes = self.project.basedata.get_table(
            'ESt_Einnahmen_pro_WE', 'Einnahmen').features().filter(
                AGS2=self.project_frame.ags[:2],
                Gemeindetyp=self.project_frame.gemeinde_typ
            )
        est_gesamt = 0
        for est_pro_we_geb_typ in est_pro_wes:
            geb_typ_id = est_pro_we_geb_typ.IDGebaeudetyp
            anzahl_we = sum(
                self.we.filter(id_gebaeudetyp=geb_typ_id).values('we'))
            est = anzahl_we * est_pro_we_geb_typ.ESt_pro_WE
            est_gesamt += est
        project_gem = self.wanderung.get(AGS=self.project_frame.ags)
        est_pro_ew = est_gesamt / project_gem.zuzug

        for gem in self.bilanzen:
            wanderung = self.wanderung.get(AGS=gem.AGS)
            if not wanderung:
                est = 0
            else:
                est = est_pro_ew * wanderung.saldo
                rnd = 1000 if abs(est) >= 500 else 100
                est = round(est/rnd) * rnd
            gem.einkommensteuer = est
            gem.save()

        return True


class FamAusgleichCalculation(Worker):
    '''
    calculation of family compensation
    '''
    def __init__(self, project, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.project = project
        self.bilanzen = Gemeindebilanzen.features(project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]

    def work(self):
        self.log('Berechne Familienleistungsausgleich...')
        fla_factor = self.project.basedata.get_table(
            'FLA_Landesfaktoren', 'Einnahmen').features().get(
                AGS_Land=self.project_frame.ags[:2]
            ).FLA_Faktor

        for gem in self.bilanzen:
            fla = gem.einkommensteuer * fla_factor
            rnd = 1000 if abs(fla) >= 500 else 100
            fla = round(fla/rnd) * rnd
            gem.fam_leistungs_ausgleich = fla
            gem.save()

        return True


class GewerbesteuerCalculation(Worker):
    '''
    calculation of business tax
    '''
    def __init__(self, project, parent=None):
        '''
        Parameters
        ----------
        project : Poject
            the project
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        super().__init__(parent=parent)
        self.project = project
        self.bilanzen = Gemeindebilanzen.features(project=project)
        self.wanderung = BeschaeftigtenWanderung.features(project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.areas = Teilflaechen.features(project=project)
        self.gewerbe_anteile = Gewerbeanteile.features(project=project)
        self.verkaufsflaechen = Verkaufsflaechen.features(project=project)

    def work(self):
        self.log('Berechne Gewerbesteuer...')
        messbetrag_g, svb_g = self.calc_messbetrag_gewerbe()
        messbetrag_eh, svb_eh = self.calc_messbetrag_einzelhandel()
        messbetrag_pro_svb = (messbetrag_g + messbetrag_eh) / (svb_g + svb_eh)

        for gem in self.bilanzen:
            wanderung = self.wanderung.get(AGS=gem.AGS)
            bvv_plus_lvv_plus_ehz = self.project.basedata.get_table(
                'GewSt_Umlage_Vervielfaeltiger', 'Einnahmen').features().get(
                    AGS_Land=gem.AGS[:2]
                ).Summe_BVV_LVV_EHZ

            if not wanderung:
                gst = 0
            else:
                saldo = wanderung.saldo
                if gem.AGS == self.project_frame.ags:
                    saldo += svb_eh
                gst = (messbetrag_pro_svb * gem.Hebesatz_GewSt / 100 * saldo *
                       (1 - bvv_plus_lvv_plus_ehz / gem.Hebesatz_GewSt))
                rnd = 1000 if gst >= 500 else 100
                gst = round(gst/rnd) * rnd
            gem.gewerbesteuer = gst
            gem.save()

        return True

    def calc_messbetrag_gewerbe(self):
        '''
        base rate for businesses
        '''
        messzahlen = self.project.basedata.get_table(
            'GewSt_Messbetrag_pro_Arbeitsplatz', 'Einnahmen').features().filter(
                AGS2=self.project_frame.ags[:2])
        messbetrag_sum = 0
        svb_sum = 0
        gewerbe_areas = self.areas.filter(nutzungsart=Nutzungsart.GEWERBE.value)
        for area in gewerbe_areas:
            anteile = self.gewerbe_anteile.filter(id_teilflaeche=area.id)
            estimated = sum(anteile.values('anzahl_jobs_schaetzung'))
            svb = area.ap_gesamt
            svb_sum += svb
            cor_factor = svb / estimated if estimated > 0 else 0
            for anteil in anteile:
                m_bt = messzahlen.get(IDBranche=anteil.id_branche)
                betrag = (anteil.anzahl_jobs_schaetzung * cor_factor *
                          m_bt.GewStMessbetrag_pro_Arbeitsplatz)
                messbetrag_sum += betrag
        self.areas.filter()
        return messbetrag_sum, svb_sum

    def calc_messbetrag_einzelhandel(self):
        '''
        base rate for retail trade
        '''
        messzahlen = self.project.basedata.get_table(
            'GewSt_Messbetrag_und_SvB_pro_qm_Verkaufsflaeche',
            'Einnahmen').features()
        df_vkfl = self.verkaufsflaechen.to_pandas()
        messbetrag_sum = 0
        svb_sum = 0
        for id_sortiment, vkfl in df_vkfl.groupby('id_sortiment'):
            m_s = messzahlen.get(ID_Sortiment=id_sortiment)
            vkfl_sum = vkfl['verkaufsflaeche_qm'].sum()
            betrag = (vkfl_sum * m_s.GewStMessbetrag_pro_qm_Verkaufsflaeche)
            svb = (vkfl_sum * m_s.SvB_pro_qm_Verkaufsflaeche)
            messbetrag_sum += betrag
            svb_sum += svb
        return messbetrag_sum, svb_sum

