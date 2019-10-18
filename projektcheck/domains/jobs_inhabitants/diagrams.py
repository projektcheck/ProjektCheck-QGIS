# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.ticker as mticker
import pandas as pd

from projektcheck.base.diagrams import MatplotDiagram
from projektcheck.domains.jobs_inhabitants.tables import WohnenProJahr


class BewohnerEntwicklung(MatplotDiagram):
    def create(self, **kwargs):
        area = kwargs['area']
        flaechen_name = area.name

        features = WohnenProJahr.features().filter(id_teilflaeche=area.id)
        df = features.to_pandas()
        groups = df['altersklasse'].unique()
        colors = self.plt.cm.viridis_r(np.linspace(0, 1, len(groups)))
        transformed = pd.DataFrame(columns=groups)

        grouped = df.groupby(by='altersklasse')
        for name, group_data in grouped:
            group_data.sort_values('jahr', inplace=True)
            transformed[name] = group_data['bewohner'].values
        xticks = df['jahr'].unique()
        xticks.sort()
        ax = transformed.plot(kind='bar', stacked=True, figsize=(16, 8),
                              color=colors, title=self.title, grid=False)
        ax.yaxis.grid(True, which='major')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set_xticklabels(xticks, rotation=45)
        ax.set_ylabel(u'Anzahl Personen')
        ax.set_ylim(bottom=0)
        return ax


class ArbeitsplatzEntwicklung(MatplotDiagram):
    def _create(self, **kwargs):
        flaechen_id = kwargs['flaechen_id']
        flaechen_name = kwargs['flaechen_name']
        self.title = (u"{} - {}: Geschätzte Anzahl Arbeitsplätze "
                      u"(Orientierungswerte)".format(
                          self.tbx.par.get_projectname(), flaechen_name))

        flaechen_id = kwargs['flaechen_id']

        table = 'AP_nach_Jahr'
        workspace = 'FGDB_Bewohner_Arbeitsplaetze.gdb'
        table_df = self.tbx.table_to_dataframe(
            table, workspace=workspace,
            columns=['Jahr', 'AP'],
            where='IDTeilflaeche={}'.format(flaechen_id))
        table_df.sort('Jahr', inplace=True)
        ax = table_df.plot(x='Jahr', y='AP', kind='line', title=self.title,
                           color='r', legend=False, figsize=(10, 5), grid=False)
        ax.set_ylabel(u'Arbeitsplätze (Orientierungswerte)')
        ax.set_ylim(bottom=0)
        ax.yaxis.grid(True, which='major')

        return ax


class BranchenAnteile(MatplotDiagram):
    def _create(self, **kwargs):
        flaechen_id = kwargs['flaechen_id']
        flaechen_name = kwargs['flaechen_name']
        self.title = (u"{} - {}: Geschätzte Branchenanteile an den "
                      u"Arbeitsplätzen".format(
                          self.tbx.par.get_projectname(), flaechen_name))

        flaechen_id = kwargs['flaechen_id']

        table = 'Branchenanteile'
        branche_table = 'Gewerbe_Branchen'
        workspace = 'FGDB_Bewohner_Arbeitsplaetze.gdb'
        table_df = self.tbx.table_to_dataframe(
            table, workspace=workspace,
            columns=['IDBranche', 'Anteil'],
            where='IDTeilflaeche={}'.format(flaechen_id))
        branche_table_df = self.tbx.table_to_dataframe(
            branche_table, workspace='FGDB_Definition_Projekt_Tool.gdb',
            columns=['ID_Branche_Projektcheck', 'Name_Branche_Projektcheck'],
            is_base_table=True
        )
        colors = self.plt.cm.Accent(np.linspace(0, 1, len(table_df)))
        idx = table_df['Anteil'] > 0
        table_df = table_df[idx]
        colors = colors[idx]

        branche_table_df.rename(
            columns={'ID_Branche_Projektcheck': 'IDBranche'}, inplace=True)
        joined = table_df.merge(branche_table_df, on='IDBranche')
        joined['Anteil'] *= 100

        ax = joined['Anteil'].plot(kind='pie', labels=[''] * len(table_df),
                                   autopct='%.0f%%',
                                   figsize=(8, 8), title=' ',
                                   #shadow=True,
                                   #explode=[0.1] * len(table_df),
                                   colors=colors)
        #title = ax.set_title(self.title)
        #title.set_position((.5, 1.0))
        self.plt.figtext(.5, .92, self.title,
                         horizontalalignment='center',
                         fontsize=12)  #, fontweight='bold')

        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.legend(joined['Name_Branche_Projektcheck'], loc='upper center',
                  bbox_to_anchor=(0.5, 0.05))
        # didn't find a way to pass custom colors directly
        for color, handle in zip(colors, ax.get_legend().legendHandles):
            handle.set_linewidth(2.0)
            handle.set_color(color)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.y0 * 0.5, box.width, box.height])

        return ax
