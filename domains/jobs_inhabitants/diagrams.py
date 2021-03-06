# -*- coding: utf-8 -*-
'''
***************************************************************************
    diagrams.py
    ---------------------
    Date                 : October 2019
    Copyright            : (C) 2019 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

diagrams showing the structure and development of inhabitants and jobs
'''

__author__ = 'Christoph Franke'
__date__ = '18/10/2019'
__copyright__ = 'Copyright 2019, HafenCity University Hamburg'

import numpy as np
import matplotlib
matplotlib.use('agg')
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import locale

from projektcheck.base.diagrams import MatplotDiagram
from projektcheck.base.project import ProjectManager
from projektcheck.domains.definitions.tables import Gewerbeanteile
from .tables import WohnenProJahr, ApProJahr


class BewohnerEntwicklung(MatplotDiagram):
    '''
    bar chart showing the development of the population and age groups over time
    '''
    def create(self, **kwargs):
        area = kwargs['area']

        features = WohnenProJahr.features().filter(id_teilflaeche=area.id)
        df = features.to_pandas()
        groups = df['altersklasse'].unique()
        colors = plt.cm.viridis_r(np.linspace(0, 1, len(groups)))
        transformed = pd.DataFrame(columns=groups)

        grouped = df.groupby(by='altersklasse')
        for name, group_data in grouped:
            group_data.sort_values('jahr', inplace=True)
            transformed[name] = group_data['bewohner'].values
        xticks = df['jahr'].unique()
        xticks.sort()
        figure = plt.figure()
        subplot = figure.add_subplot(111)
        ax = transformed.plot(kind='bar', stacked=True, figsize=(16, 8),
                              color=colors, title=self.title, grid=False,
                              ax=subplot)
        ax.yaxis.grid(True, which='major')
        ax.get_yaxis().set_major_formatter(mticker.FuncFormatter(
            lambda y, p: locale.format_string("%d", y, grouping=True)))
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_xticklabels(xticks, rotation=45)
        ax.set_ylabel(u'Anzahl Personen')
        ax.set_xlabel(u'Jahr')
        ax.set_ylim(bottom=0)
        figure.subplots_adjust(right=0.8)
        figure.add_axes(ax)
        return figure


class ArbeitsplatzEntwicklung(MatplotDiagram):
    '''
    line chart showing the development of the jobs
    '''
    def create(self, **kwargs):

        area = kwargs['area']

        features = ApProJahr.features().filter(id_teilflaeche=area.id)
        df = features.to_pandas()
        df.sort_values('jahr', inplace=True)
        figure = plt.figure()
        subplot = figure.add_subplot(111)
        ax = df.plot(x='jahr', y='arbeitsplaetze', kind='line',
                     title=self.title, color='r', legend=False, figsize=(10, 5),
                     grid=False, ax=subplot)
        ax.set_ylabel(u'Arbeitsplätze (Orientierungswerte)')
        ax.get_yaxis().set_major_formatter(mticker.FuncFormatter(
            lambda y, p: locale.format_string("%d", y, grouping=True)))
        ax.set_xlabel(u'Jahr')
        ax.set_ylim(bottom=0)
        ax.yaxis.grid(True, which='major')
        return figure


class BranchenAnteile(MatplotDiagram):
    '''
    pie chart showing the shares of branches of industry
    '''
    def create(self, **kwargs):

        area = kwargs['area']

        features = Gewerbeanteile.features().filter(id_teilflaeche=area.id)
        df = features.to_pandas()

        basedata = ProjectManager().basedata
        df_branchen = basedata.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt'
        ).to_pandas()
        colors = plt.cm.Accent(np.linspace(0, 1, len(df)))
        idx = df['anteil_branche'] > 0
        df = df[idx]
        colors = colors[idx]

        df_branchen.rename(
            columns={'ID_Branche_ProjektCheck': 'id_branche'}, inplace=True)
        joined = df.merge(df_branchen, on='id_branche')

        figure = plt.figure()
        subplot = figure.add_subplot(111)
        ax = joined['anteil_branche'].plot(kind='pie', labels=[''] * len(df),
                                   autopct='%.0f%%',
                                   figsize=(8, 8), title=' ',
                                   #shadow=True,
                                   #explode=[0.1] * len(table_df),
                                   colors=colors,
                                   ax=subplot)
        #title = ax.set_title(self.title)
        #title.set_position((.5, 1.0))
        plt.figtext(.5, .92, self.title,
                         horizontalalignment='center',
                         fontsize=12)  #, fontweight='bold')

        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.legend(joined['Name_Branche_ProjektCheck'], loc='upper center',
                  bbox_to_anchor=(0.5, 0.05))
        # didn't find a way to pass custom colors directly
        for color, handle in zip(colors, ax.get_legend().legendHandles):
            handle.set_linewidth(2.0)
            handle.set_color(color)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.y0 * 0.5, box.width, box.height])
        figure.tight_layout()
        figure.subplots_adjust(bottom=0.2)

        return figure
