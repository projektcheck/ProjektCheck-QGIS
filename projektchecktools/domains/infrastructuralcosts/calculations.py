# -*- coding: utf-8 -*-
'''
***************************************************************************
    calculations.py
    ---------------------
    Date                 : February 2020
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

workers for calculations in the infrastructural costs domain
'''

__author__ = 'Christoph Franke'
__date__ = '06/02/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

from projektchecktools.base.domain import Worker
from projektchecktools.base.project import Project
from projektchecktools.utils.utils import round_df_to
from projektchecktools.domains.definitions.tables import Projektrahmendaten

from .tables import (KostenkennwerteLinienelemente, ErschliessungsnetzLinien,
                     ErschliessungsnetzPunkte, Kostenaufteilung,
                     Gesamtkosten, GesamtkostenTraeger)

import time
import pandas as pd
import numpy as np

def init_kostenkennwerte(project: Project) -> pd.DataFrame:
    '''
    fills the project table holding the costs of line elements with defaults
    based on region and year
    '''
    kk_features = KostenkennwerteLinienelemente.features(create=True)
    kk_features.delete()

    # calculate time factor
    current_year = int(time.strftime("%Y"))

    df_frame_data = project.basedata.get_table(
        'Rahmendaten', 'Kosten').to_pandas()
    df_networks = project.basedata.get_table(
        'Netze_und_Netzelemente', 'Kosten').to_pandas()
    gemeinden = project.basedata.get_table(
        'bkg_gemeinden', 'Basisdaten_deutschland').features()

    interest = df_frame_data['Zins']
    reference_year = df_frame_data['Stand_Kostenkennwerte']
    time_factor = (1 + interest) ** (current_year - reference_year)
    # get regional factor
    ags = Projektrahmendaten.get_table(project=project)[0]['ags']
    gemeinde = gemeinden.get(AGS=ags)
    regional_factor = gemeinde.BKI_Regionalfaktor
    # fill table Kostenkennwerte_Linienelemente
    regional_time_factor = time_factor * regional_factor
    rounding_factor = 5
    # multiply with factors
    df_networks.loc[:, ['Euro_EH', 'Cent_BU', 'Euro_EN']] *= \
        regional_time_factor[0]
    # round to 5
    df_networks.fillna(0, inplace=True)
    df_networks.loc[:, ['Euro_EH', 'Cent_BU', 'Euro_EN']] = \
        round_df_to(df_networks.loc[:, ['Euro_EH', 'Cent_BU', 'Euro_EN']],
                    rounding_factor)

    del df_networks['fid']
    kk_features.update_pandas(df_networks)
    return kk_features


class GesamtkostenErmitteln(Worker):
    '''
    worker for estimating the total (gross) costs of the infrastucture network
    '''
    # period of estimation
    years = 25

    def __init__(self, project, parent=None):
        super().__init__(parent=parent)
        self.project = project

    def work(self):
        self.log('Bereite Ausgangsdaten auf...')
        kk_features = KostenkennwerteLinienelemente.features(create=True)
        if len(kk_features) == 0:
            init_kostenkennwerte(self.project)
        self.df_costs = kk_features.to_pandas()
        del self.df_costs['IDNetz']
        self.df_lines = ErschliessungsnetzLinien.features(
            project=self.project).to_pandas()
        self.df_points = ErschliessungsnetzPunkte.features(
            project=self.project).to_pandas()
        self.joined_lines_costs = self.df_lines.merge(
            self.df_costs, on='IDNetzelement', how='left')

        # the net elements are just needed for their names
        self.df_elements = self.project.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten',
            fields=['IDNetz', 'Netz']).to_pandas()
        # duplicate entries for 'IDNetz'/'Netz' combinationsjean
        del self.df_elements['fid']
        self.df_elements.drop_duplicates(inplace=True)

        self.df_phases = self.project.basedata.get_table(
            'Kostenphasen', 'Kosten').to_pandas()

        self.log('Berechne Gesamtkosten der Phasen {}<br>{}...'.format(
            f' für die ersten {self.years} Jahre'.format(),
            ', <br>'.join(self.df_phases['Kostenphase'].tolist())
        ))

        self.costs_results = Gesamtkosten.features(
            project=self.project, create=True)
        self.costs_results.delete()
        df_results = self.calculate_phases()
        del df_results['fid']
        self.costs_results.update_pandas(df_results)

    def calculate_phases(self):
        '''
        calculate costs of each phase
        '''
        df_results = self.costs_results.to_pandas()

        # points and lines have same columns and calc. basis is same as well
        grouped_lines = self.joined_lines_costs.groupby('IDNetz')
        grouped_points = self.df_points.groupby('IDNetz')
        for grouped in [grouped_lines, grouped_points]:
            for net_id, group in grouped:
                for index, phase in self.df_phases.iterrows():
                    phase_id = phase['IDKostenphase']
                    if phase_id == 1:
                        costs = group['Euro_EH']
                    elif phase_id == 2:
                        costs = self.years * group['Cent_BU'] / 100.
                    elif phase_id == 3:
                        costs = (self.years *
                                 group['Euro_EN'] / group['Lebensdauer'])
                    else:
                        raise Exception(f'phase {phase_id} not defined')

                    # only difference between points and lines: costs of lines
                    # are based on costs per meter, points naturally don't have
                    # a length at all ^^
                    if 'length' in group:
                        costs *= group['length']
                    costs = costs.sum()

                    row = pd.DataFrame({'IDNetz': net_id,
                                        'IDKostenphase': phase_id,
                                        'Euro': round(costs, 2),
                                        }, index=[0])
                    df_results = df_results.append(row, ignore_index=True)

        df_results = df_results.groupby(['IDNetz', 'IDKostenphase']).agg(np.sum)
        df_results.reset_index(inplace=True)
        df_results = df_results.merge(self.df_phases, on='IDKostenphase')
        df_results = df_results.merge(self.df_elements, on='IDNetz')
        return df_results


class KostentraegerAuswerten(Worker):
    '''
    worker for calculating the infrastuctural costs per payer
    '''
    def __init__(self, project, parent=None):
        super().__init__(parent=parent)
        self.project = project

    def work(self):
        self.log('Ermittle Gesamtkosten...')
        gesamtkosten_worker = GesamtkostenErmitteln(
            self.project, parent=self.parent())
        gesamtkosten_worker.work()

        self.shares_results = GesamtkostenTraeger.features(
            project=self.project, create=True)
        self.df_shares = Kostenaufteilung.features(
            create=True).to_pandas()
        self.log('Berechne Aufteilung der Kosten nach Kostenträgern...')

        self.df_elements = self.project.basedata.get_table(
            'Netze_und_Netzelemente', 'Kosten',
            fields=['IDNetz', 'Netz']).to_pandas()
        # duplicate entries for 'IDNetz'/'Netz' combinations
        del self.df_elements['fid']
        self.df_elements.drop_duplicates(inplace=True)

        self.shares_results.delete()
        df_results = self.calculate_shares()
        self.shares_results.update_pandas(df_results)

    def calculate_shares(self):
        '''
        calculate shares of costs per payer
        '''
        df_costs = Gesamtkosten.features(project=self.project).to_pandas()
        joined = df_costs.merge(self.df_shares,
                                on=['IDNetz', 'IDKostenphase'],
                                how='right')
        joined.fillna(0, inplace=True)
        joined['Betrag_GSB'] = (joined['Euro'] *
                                joined['Anteil_GSB'] / 100.).round(2)
        joined['Betrag_GEM'] = (joined['Euro'] *
                                joined['Anteil_GEM'] / 100.).round(2)
        joined['Betrag_ALL'] = (joined['Euro'] *
                                joined['Anteil_ALL'] / 100.).round(2)
        summed = joined.groupby('IDNetz').sum()
        summed.reset_index(inplace=True)

        summed = summed.merge(self.df_elements, on='IDNetz')
        return summed