# -*- coding: utf-8 -*-
#from rpctools.utils.config import Folders, Config
#from rpctools.utils.spatial_lib import clip_raster
#from rpctools.utils.spatial_lib import Point
#from rpctools.utils.params import DummyTbx

import os
import numpy as np
import pandas as pd


class Sales:
    NULLFALL = 0
    PLANFALL = 1
    # time to separate same markets into 'Umfeld' and 'Abstand'
    # example: cut_off_time = 5 min
    #          nearest market = 4 min drive -> 'Umfeld'
    #          second market = 7 min drive -> 'Umfeld'
    #          third market = 12 min drive -> 'Abstand'
    # Note: switched from times to km -> cutoff is > 1 km
    relation_dist = 1  # km

    def __init__(self, basedata, df_relations, df_markets, df_cells,
                 debug=False):
        self.basedata = basedata
        self.df_relations = df_relations
        self.df_markets = df_markets
        self.df_cells = df_cells

    def calculate_nullfall(self):
        return self._calculate_sales(self.NULLFALL)

    def calculate_planfall(self):
        return self._calculate_sales(self.PLANFALL)

    def _calculate_sales(self, setting):
        df_markets = self._prepare_markets(self.df_markets, setting)
        df_markets.set_index('id', inplace=True)

        # drop rows with markets, that are not in the dataframe of markets
        # used for current settings
        # (e.g. planfall markets when current setting is nullfall)
        ids_not_in_df = np.setdiff1d(
            np.unique(self.df_relations['id_markt']), df_markets.index)
        df_relations = self.df_relations.drop(
            self.df_relations.index[np.in1d(self.df_relations['id_markt'],
                                            ids_not_in_df)])

        # easiest way to distinguish same distances by adding
        # normed bee-lines
        beelines = df_relations['luftlinie']
        beelines[df_relations['distanz'] == -1] = -1
        beelines_norm = beelines / beelines.max()
        df_relations['distanz'] += beelines_norm

        # calc with distances in kilometers
        df_relations['distanz'] /= 1000
        n_idx = df_relations['distanz'] < 0
        df_relations['distanz'][n_idx] = -1

        # in case of Nullfall take zensus points without planned areas
        df_cells = self.df_cells[self.df_cells['id_teilflaeche'] < 0] \
            if setting == self.NULLFALL else self.df_cells

        df_kk = pd.DataFrame()
        df_kk['id_siedlungszelle'] = df_cells['id']
        df_kk['kk'] = df_cells['kk']
        kk_merged = df_relations.merge(df_kk, on='id_siedlungszelle')

        kk_matrix = kk_merged.pivot(index='id_markt',
                                    columns='id_siedlungszelle',
                                    values='kk')

        dist_matrix = kk_merged.pivot(index='id_markt',
                                      columns='id_siedlungszelle',
                                      values='distanz')
        dist_matrix = dist_matrix.fillna(0)

        attraction_matrix = pd.DataFrame(data=np.zeros(dist_matrix.shape),
                                         index=dist_matrix.index,
                                         columns=dist_matrix.columns)

        for index, market in df_markets.iterrows():
            dist = dist_matrix.loc[index]
            factor = market['exp_faktor']
            exponent = market['exponent']
            attraction_matrix.loc[index] = factor * np.exp(dist * exponent)

        unreachable = dist_matrix < 0
        attraction_matrix[unreachable] = 0
        betriebstyp_col = 'id_betriebstyp_nullfall' \
            if setting == self.NULLFALL else 'id_betriebstyp_planfall'

        masked_dist_matrix = dist_matrix.T
        masked_dist_matrix = masked_dist_matrix.mask(masked_dist_matrix < 0)

        # local providers
        # no real competition, but only closest three per cell (copy/paste from
        # calc_competitors, had no time seperate implementation)
        is_lp = df_markets[betriebstyp_col] == 1
        local_markets = df_markets[is_lp]
        local_masked_dist = masked_dist_matrix[local_markets.index]
        df_ranking = local_masked_dist.rank(axis=1, method='first')
        local_comp_matrix = pd.DataFrame(data=0, index=df_ranking.index,
                                         columns=df_ranking.columns)
        local_comp_matrix[df_ranking <= 3] = 1
        local_comp_matrix[np.isnan(df_ranking)] = 0
        local_comp_matrix = local_comp_matrix.T

        # small markets
        is_sm = df_markets[betriebstyp_col] == 2
        small_markets = df_markets[is_sm]
        small_comp_matrix = self.calc_competitors(
            masked_dist_matrix, small_markets)

        # big markets
        big_markets = df_markets[df_markets[betriebstyp_col] > 2]
        big_comp_matrix = self.calc_competitors(
            masked_dist_matrix, big_markets)

        # merge
        big_comp_matrix.loc[is_lp] = local_comp_matrix
        big_comp_matrix.loc[is_sm] = small_comp_matrix.loc[is_sm]

        competitor_matrix = big_comp_matrix
        competitor_matrix[dist_matrix < 0] = 0

        #if self.debug:
            #setting_str = 'Nullfall' if setting == self.NULLFALL else 'Planfall'
            #self.log('DEBUG: Schreibe Zwischenergebnisse')
            #if setting == self.NULLFALL:
                #self.write_intermediate_results(dist_matrix.transpose(),
                                                #'Distanzmatrix')
            #self.write_intermediate_results(
                #attraction_matrix.transpose(),
                #u'{}_erstes_Zwischenergebnis_KK_Anteile_Wahrsch'.format(setting_str))
            #self.write_intermediate_results(
                #competitor_matrix.transpose(),
                #u'{}_zweites_Zwischenergebnis_Attraktivitaet'.format(setting_str))
            #self.log('DEBUG: Berechnung')

        # include competition between same market types in attraction_matrix
        attraction_matrix *= competitor_matrix.values

        probabilities = attraction_matrix / attraction_matrix.sum(axis=0)
        kk_flow = probabilities * kk_matrix
        kk_flow = kk_flow.fillna(0)

        #if self.debug:
            #self.log('DEBUG: Schreibe weitere Zwischenergebnisse')
            #self.write_intermediate_results(
                #attraction_matrix.transpose(),
                #u'{}_drittes_Zwischenergebnis_Verteilungsmassstab_erster_Schritt'.format(setting_str))
            #self.write_intermediate_results(
                #probabilities.transpose(),
                #u'{}_viertes_Zwischenergebnis_Verteilungsmassstab_zweiter_Schritt'.format(setting_str))
            #self.write_intermediate_results(
                #kk_flow.transpose(),
                #u'{}_fuenftes_Zwischenergebnis_Kaufkraftstroeme'.format(setting_str))

        return kk_flow

    #def write_intermediate_results(self, dataframe, table):
        #self.tbx.insert_dataframe_in_table(
            #table, dataframe.reset_index(),
            #workspace='FGDB_Standortkonkurrenz_Supermaerkte.gdb',
            #create=True)

    def calc_competitors(self, masked_dist_matrix, df_markets):
        """
        account competition through other markets of the same brand
        """
        cutoff_dist = self.relation_dist
        results = pd.DataFrame(data=1., index=masked_dist_matrix.index,
                               columns=masked_dist_matrix.columns)
        competing_markets = df_markets[['id_kette']]
        for id_kette in np.unique(competing_markets['id_kette']):
            markets_of_same_type = \
                competing_markets[competing_markets['id_kette'] == id_kette]
            if len(markets_of_same_type['id_kette']) == 1 or id_kette == 0:
                continue
            indices = list(markets_of_same_type.index)
            same_type_dist_matrix = masked_dist_matrix[indices]
            df_ranking = same_type_dist_matrix.rank(axis=1, method='first')
            nearest_three_mask = df_ranking <= 3
            df_ranking = df_ranking.mask((nearest_three_mask==False))
            cutoff_dist_matrix = same_type_dist_matrix.copy()
            cutoff_dist_matrix['Minimum'] = \
                cutoff_dist_matrix.loc[:, indices].min(axis=1)
            # differences between way to nearest market and other markets
            # set all distances relative to nearest market
            cutoff_dist_matrix = cutoff_dist_matrix.sub(
                cutoff_dist_matrix['Minimum'], axis=0)
            del cutoff_dist_matrix['Minimum']
            cutoff_dist_matrix = cutoff_dist_matrix.mask(
                (nearest_three_mask==False))
            cutoff_dist_matrix =  cutoff_dist_matrix.round(2)
            #is_near = cutoff_dist_matrix <= cutoff_dist
            is_near = np.logical_or(cutoff_dist_matrix < cutoff_dist,
                                    np.isclose(cutoff_dist_matrix, cutoff_dist))
            df_ranking['Umkreis'] = is_near.sum(axis=1)
            #same_type_dist_ranking['Abstand'] = \
                #number_of_competing_markets - is_near['Umkreis']
            for market_id in indices:
                # note: is_near[market_id] indicates if market
                #       is in 'Umkreis' (meaning is one of the nearest markets)
                # write data for near markets with:
                # -> 1 near market
                factor = df_markets.loc[market_id]['ein_Markt_in_Naehe']
                results.loc[np.logical_and(is_near[market_id]==True,
                                           df_ranking['Umkreis']==1),
                            market_id] = factor
                # -> 2 near markets
                factor = df_markets.loc[market_id]['zwei_Maerkte_in_Naehe']
                results.loc[np.logical_and(is_near[market_id]==True,
                                            df_ranking['Umkreis']==2),
                            market_id] = factor
                # -> more than 2 near markets
                factor = df_markets.loc[market_id]['drei_Maerkte_in_Naehe']
                results.loc[np.logical_and(is_near[market_id]==True,
                                           df_ranking['Umkreis']==3),
                            market_id] = factor
                # write data for far markets with:
                # -> market is far; 1 near market exists;
                # market is closer than posible other far markets
                factor = df_markets.loc[market_id]\
                    ['zweiter_Markt_mit_Abstand_zum_ersten']
                results.loc[np.logical_and(
                    is_near[market_id]==False,
                    np.logical_and(df_ranking['Umkreis']==1,
                                   df_ranking[market_id]==2)),
                            market_id] = factor
                # -> market is far; 1 near market exists;
                # another far market exists that is closer to cell
                factor = df_markets.loc[market_id]\
                    ['dritter_Markt_mit_Abstand_zum_ersten']
                results.loc[np.logical_and(
                    is_near[market_id]==False,
                    np.logical_and(df_ranking['Umkreis']==1,
                                   df_ranking[market_id]==3)),
                            market_id] = factor
                # -> market is far, 2 near markets
                factor = df_markets.loc[market_id]\
                    ['dritter_Markt_mit_Abstand_zum_ersten_und_zweiten']
                results.loc[np.logical_and(is_near[market_id]==False,
                                           df_ranking['Umkreis']==2),
                            market_id] = factor
            # if more than 3 markets: markets 4 to end set to 0
            # if market 3 and 4 have same distance: keep both
            results.loc[:, (indices)] = results.loc[:, indices].mask(
                nearest_three_mask==False, 0.)
        # Return results in shape of dist_matrix
        res = results.T
        return res

    def get_dist_matrix(self):
        # Dataframe for distances
        dist_matrix = self.df_relations.pivot(index='id_markt',
                                           columns='id_siedlungszelle',
                                           values='distanz')
        return dist_matrix

    def _prepare_markets(self, df_markets, setting):
        """
        setting - nullfall or planfall
        """
        betriebstyp_col = 'id_betriebstyp_nullfall' \
            if setting == self.NULLFALL else 'id_betriebstyp_planfall'

        # ignore markets that don't exist yet resp. are closed
        ags = np.unique(df_markets['AGS'])
        df_markets = df_markets[df_markets[betriebstyp_col] != 0]

        communities = self.basedata.get_table(
            'bkg_gemeinden', 'Basisdaten_deutschland',
            fields=['AGS', 'vwg_groessenklasse'])
        communities.filter(AGS__in=list(ags))
        df_communities = communities.to_pandas()

        # add groessenklassen to markets
        df_markets = df_markets.merge(df_communities, on='AGS')

        # dataframe for exponential parameters
        df_exponential_parameters = self.basedata.get_table(
            'Exponentialfaktoren', 'Standortkonkurrenz_Supermaerkte',
            fields=['gem_groessenklasse', 'id_kette', 'id_betriebstyp',
                    'exponent', 'exp_faktor']).to_pandas()

        df_attractivity_factors = self.basedata.get_table(
            'Attraktivitaetsfaktoren', 'Standortkonkurrenz_Supermaerkte'
            ).to_pandas()

        attractivity_cols = ['ein_Markt_in_Naehe', 'zwei_Maerkte_in_Naehe',
                             'drei_Maerkte_in_Naehe',
                             'zweiter_Markt_mit_Abstand_zum_ersten',
                             'dritter_Markt_mit_Abstand_zum_ersten',
                             'dritter_Markt_mit_Abstand_zum_ersten_und_zweiten']

        # add columns to markets
        df_markets['exponent'] = 0
        df_markets['exp_faktor'] = 0
        for col in attractivity_cols:
            df_markets[col] = 0

        # add the parameters to markets
        for index, market in df_markets.iterrows():
            gr_klasse = int(market['vwg_groessenklasse'])
            id_kette = market['id_kette']
            id_betriebstyp = market[betriebstyp_col]

            def get_entry_idx(df, id_kette, id_betriebstyp):
                '''look up for an entry in given df and return index
                (default if special one not found),
                scheme is the same for tables attractivity and exp. factors'''
                # look for entry of combination kette/betriebstyp
                idx = np.logical_and(
                    df['id_kette'] == id_kette,
                    df['id_betriebstyp'] == id_betriebstyp)
                # take the default entry for kette if combination is not found
                if idx.sum() == 0:
                    idx = np.logical_and(
                        df['id_kette'] == 0,
                        df['id_betriebstyp'] == id_betriebstyp)
                return idx

            # exp. factors
            df_exp_gr_klasse = df_exponential_parameters[
                df_exponential_parameters['gem_groessenklasse'] == gr_klasse]
            idx = get_entry_idx(df_exp_gr_klasse, id_kette, id_betriebstyp)
            entry = df_exp_gr_klasse[idx]
            df_markets.loc[index, 'exponent'] = entry['exponent'].values[0]
            df_markets.loc[index, 'exp_faktor'] = entry['exp_faktor'].values[0]

            # attractivity
            idx = get_entry_idx(df_attractivity_factors,
                                id_kette, id_betriebstyp)
            entry = df_attractivity_factors[idx]
            for col in attractivity_cols:
                df_markets.loc[index, col] = entry[col].values[0]

        return df_markets






