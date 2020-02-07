# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from textwrap import wrap

from projektcheck.domains.constants import Nutzungsart
from projektcheck.base.diagrams import MatplotDiagram
from projektcheck.base.project import ProjectManager
from projektcheck.domains.infrastructuralcosts.tables import (
    Gesamtkosten, GesamtkostenTraeger)


#class NetzlaengenDiagramm(MatplotDiagram):
    #def _create(self, **kwargs):
        #line_table = 'Erschliessungsnetze_Linienelemente'
        #self.title = (u"{}: Länge der zusätzlichen Infrastrukturnetze "
                 #u"(ohne punktuelle Maßnahmen)".format(
                     #self.tbx.par.get_projectname()))
        #x_label = u"Meter zusätzliche Netzlänge (ohne punktuelle Maßnahmen)"

        #linien_df = self.tbx.table_to_dataframe(
            #line_table, columns=['SHAPE_Length', 'IDNetz'],
            #workspace='FGDB_Kosten.gdb'
        #)
        #base_df = self.tbx.table_to_dataframe(
            #'Netze_und_Netzelemente', workspace='FGDB_Kosten_Tool.gdb',
            #columns=['IDNetz', 'Netz'],
            #is_base_table=True
        #)
        #base_df.drop_duplicates(inplace=True)
        #joined = linien_df.merge(base_df, on='IDNetz', how='right')
        #joined.fillna(0, inplace=True)
        #grouped = joined.groupby(by='IDNetz')
        #categories = []
        #lengths = []
        #for id_netz, grouped_df in grouped:
            #categories.append(grouped_df['Netz'].values[0])
            #lengths.append(grouped_df['SHAPE_Length'].sum())

        #figure, ax = self.plt.subplots(figsize=(10, 5))
        #ax.tick_params(axis='both', which='major', labelsize=9)
        #y_pos = np.arange(len(categories))
        #bar_width = 0.5
        #patches = ax.barh(y_pos, lengths, height=bar_width, align='center')
        ## Anfang Barlabels
        #text_offset = max([patch.get_x() + patch.get_width() for patch in
                           #patches.get_children()]) * 0.02
        #for i, patch in enumerate(patches.get_children()):
                    #width = patch.get_x() + patch.get_width()
                    #y = patch.get_y()
                    #ax.text(width + text_offset, y + bar_width/2,
                            #str(int(round(width, 0))) + u' m',
                            #color='black',ha='left', va='center')
                    ##bbox=dict(facecolor='white',
                    ## edgecolor='white', boxstyle="round"))
        #x_min, x_max = ax.get_xlim()
        #ax.set_xlim(x_min, x_max * 1.2)
        ## Ende Barlabels
        #ax.set_yticks(y_pos)
        #ax.set_yticklabels(categories)
        #ax.set_title(self.title)
        #ax.set_xlabel(x_label)
        #ax.xaxis.grid(True, which='major')
        #box = ax.get_position()
        #ax.set_position([box.x0 + box.width * 0.12, box.y0,
                         #box.width * 0.88, box.height])

        #return ax


#class MassnahmenKostenDiagramm(MatplotDiagram):

    #def _create(self, **kwargs):
        #point_table = 'Erschliessungsnetze_Punktelemente'
        #self.title = u"{}: Kosten der punktuellen Maßnahmen (nur erstmalige Herstellung)".format(
            #self.tbx.par.get_projectname())
        #x_label = u"Kosten der punktuellen Maßnahmen (nur erstmalige Herstellung)"

        #point_df = self.tbx.table_to_dataframe(
            #point_table, workspace='FGDB_Kosten.gdb')
        #base_df = self.tbx.table_to_dataframe(
            #'Netze_und_Netzelemente', workspace='FGDB_Kosten_Tool.gdb',
            #columns=['IDNetz', 'Netz'],
            #is_base_table=True
        #)
        #base_df.drop_duplicates(inplace=True)

        #joined = point_df.merge(base_df, on='IDNetz', how='right')
        #joined.fillna(0, inplace=True)
        #grouped = joined.groupby(by='IDNetz')
        #categories = []
        #costs = []
        #for id_netz, grouped_df in grouped:
            #categories.append(grouped_df['Netz'].values[0])
            #costs.append(grouped_df['Euro_EH'].sum())

        #figure, ax = self.plt.subplots(figsize=(10, 5))
        #y_pos = np.arange(len(categories))
        #bar_width = 0.5
        #patches = ax.barh(y_pos, costs, height=bar_width, align='center')
        #text_offset = max([patch.get_x() + patch.get_width() for patch in
                           #patches.get_children()]) * 0.02
        #for i, patch in enumerate(patches.get_children()):
            #width = patch.get_x() + patch.get_width()
            #y = patch.get_y() + bar_width / 2
            #ax.text(width + text_offset, y, str(int(round(width, 0))) + u' €',
                    #color='black',ha='left', va='center')
            ##bbox=dict(facecolor='white', edgecolor='white', boxstyle="round"))
        #x_min, x_max = ax.get_xlim()
        #ax.set_xlim(x_min, x_max * 1.2)


        #ax.set_yticks(y_pos)
        #ax.set_yticklabels(categories)
        #ax.set_title(self.title)
        #ax.set_xlabel(x_label)
        #ax.xaxis.set_major_formatter(mticker.FormatStrFormatter(u'%d €'))
        #ax.xaxis.grid(True, which='major')
        #box = ax.get_position()
        #ax.set_position([box.x0 + box.width * 0.12, box.y0,
                         #box.width * 0.88, box.height])

        #return ax


class GesamtkostenDiagramm(MatplotDiagram):

    def create(self, **kwargs):
        years = kwargs.get('years', 20)
        project = kwargs.get('project', ProjectManager().active_project)
        legend = ['1 - Kosten der erstmaligen Herstellung',
                  '2 - Kosten für Betrieb und Unterhaltung in den '
                  f'ersten {years} Jahren',
                  '3 - Anteilige Kosten der Erneuerung (bezogen auf '
                  f'einen Zeitraum von {years} Jahren)']
        self.title = (f"{project.name}: Gesamtkosten der infrastrukturellen "
                      f"Maßnahmen in den ersten {years} Jahren")
        x_label = u"Kosten für Netzerweiterungen und punktuelle Maßnahmen"

        df_costs = Gesamtkosten.get_table(project=project).to_pandas()

        u, u_idx = np.unique(df_costs['Netz'], return_index=True)
        categories = df_costs['Netz'][np.sort(u_idx)]

        pos_idx = np.arange(len(categories))

        bar_width = 0.2
        spacing = 1.15

        figure, ax = plt.subplots(figsize=(10, 6))
        plt.gca().invert_yaxis()
        grouped = df_costs.groupby(by='IDKostenphase')
        phase_names = []

        text_offset =  max(df_costs['Euro']) * 0.07
        for i, (phase_id, group) in enumerate(grouped):
            costs = group['Euro'].values
            patches = ax.barh(pos_idx + i * bar_width * spacing, costs,
                              height=bar_width, align='center')
            phase_names.append(legend[group['IDKostenphase'].values[0]-1])

            for index, patch in enumerate(patches):
                width = patch.get_width()
                ax.text(width + text_offset,
                        pos_idx[index] + i * bar_width * spacing,
                        '%d' % int(width) + u' €', ha='center', va='center')
                        # bbox=dict(facecolor='white',
                        # edgecolor='white', boxstyle="round"))

        ax.tick_params(axis='both', which='major', labelsize=9)
        ax.set_yticks(pos_idx + bar_width*spacing)
        ax.set_yticklabels(categories)
        ax.set_title(self.title)
        ax.set_xlabel(x_label)
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter(u'%d €'))
        ax.xaxis.grid(True, which='major')
        xmin, xmax = ax.get_xlim()
        ax.set_xlim(left=None, right=xmax*1.1, emit=True, auto=False)


        #ax.legend(phase_names, loc='upper right')
        box = ax.get_position()

        ax.set_position([box.x0 + box.width * 0.12, box.y0 + box.height * 0.2,
                         box.width * 0.88, box.height * 0.8])

        # Put a legend to the right of the current axis
        ax.legend(phase_names, loc='center left', bbox_to_anchor=(0, -0.3))
        return figure

#def format_func(x, pos):
    #s = '{:0,d}'.format(int(x))
    #return s


class KostentraegerDiagramm(MatplotDiagram):
    colors = ['#005CE6', '#002673', '#894444', '#73FFDF', '#FFFF00']

    def create(self, **kwargs):
        project = kwargs.get('project', ProjectManager().active_project)
        years = kwargs.get('years', 20)
        self.title = (f'{project.name}: Aufteilung der Gesamtkosten '
                      'auf die Kostenträger')
        y_label = ('Kosten der erstmaligen Herstellung, \n'
                   'Betriebs- und Unterhaltungskosten in den \n'
                   f'ersten {years} Jahren sowie Erneuerungskosten \n'
                   f'(anteilig für die ersten {years} Jahre)')

        df_shares = GesamtkostenTraeger.get_table(project=project).to_pandas()

        df_shareholders = project.basedata.get_table(
            'Kostentraeger', 'Kosten').to_pandas()
        categories = df_shareholders['Kostentraeger']
        cols = df_shareholders['spalte']

        pos_idx = np.arange(len(categories))

        figure, ax = plt.subplots(figsize=(12, 5))
        colors = self.colors

        summed = np.zeros(len(cols))

        for j, (index, net_share) in enumerate(df_shares.iterrows()):
            data = []
            for i, col in enumerate(cols):
                data.append(net_share[col])
            patches = ax.bar(pos_idx, data, bottom=summed, color=colors[j])
            for i, rect in enumerate(patches.get_children()):
                value = data[i]
                bottom = summed[i]
                if value != 0:
                    color = 'black'
                    if j in [1, 2]:
                        color = 'white'
                    ax.text(i, bottom + value/2., u"{0:,} €".format(int(value)),
                            ha='center', va='center', color=color)

            summed += data

        ax.set_xticks(pos_idx)
        ax.set_xticklabels(categories)
        ax.set_title(self.title)
        ax.set_ylabel(y_label, rotation=90, labelpad=15)
        fmt = u'{x:,.0f} €'
        tick = mticker.StrMethodFormatter(fmt)
        ax.yaxis.set_major_formatter(tick)
        ax.yaxis.grid(True, which='major')

        box = ax.get_position()
        ax.set_position([box.x0 + box.width * 0.2, box.y0 + box.height * 0.25,
                         box.width * 0.8, box.height * 0.75])

        # Put the legend to the right of the current axis
        ax.legend(df_shares['Netz'], loc='center left',
                  bbox_to_anchor=(0, -0.35))
        # didn't find a way to pass custom colors directly
        for color, handle in zip(colors, ax.get_legend().legendHandles):
            handle.set_color(color)
        return figure


#class VergleichsDiagramm(MatplotDiagram):
    #_column = None
    #_type_of_use = Nutzungsart.UNDEFINIERT


    #def _create(self, **kwargs):
        #self.title = (u'Vergleich: Erschließungskosten pro {} '
                      #u'(in den ersten 25 Jahren)'.format(self._unit))
        #x_label = (u'Gesamtkosten der Erschließung pro {} '
                   #u'(in den ersten 25 Jahren)'.format(self._unit))

        #df_areas = self.tbx.table_to_dataframe(
            #'Teilflaechen_Plangebiet',
            #workspace='FGDB_Definition_Projekt.gdb',
            #columns=[self._column],
            #where='Nutzungsart={}'.format(self._type_of_use)
        #)
        #df_reference = self.tbx.table_to_dataframe(
            #'Vergleichswerte',
            #workspace='FGDB_Kosten_Tool.gdb',
            #where='IDNutzungsart={}'.format(self._type_of_use),
            #is_base_table=True
        #)
        #df_costs = self.tbx.table_to_dataframe(
            #'Gesamtkosten',
            #workspace='FGDB_Kosten.gdb'
        #)

        ## there is only one row for each type of use
        #df_reference = df_reference.iloc[0]
        #x = df_areas[self._column].sum()
        #total_costs = df_costs['Euro'].sum()
        #costs_per_x = int((total_costs / x) / 1000) * 1000
        #reference = df_reference['Wert']

        #categories = [
            #u'Vergleichswert (Schätzung):\n{}'
            #.format(df_reference['Beschreibung']),
            #u'Projekt "{}" (alle Netze, \nKostenphasen und Kostenträger)'
            #.format(self.tbx.par.get_projectname())
        #]
        #categories = ['\n'.join(wrap(c, 40)) for c in categories]

        #figure, ax = self.plt.subplots(figsize=(9, 4))
        #y_pos = np.arange(len(categories))
        #bar_width = 0.5
        #patches = ax.barh(y_pos, [reference, costs_per_x], height=bar_width,
                #align='center')  #, color=[ '#99aaff', '#2c64ff'])
        ## Anfang Barlabels
        #text_offset = max([patch.get_x() + patch.get_width() for patch in
                           #patches.get_children()]) * 0.02
        #for i, patch in enumerate(patches.get_children()):
                    #width = patch.get_x() + patch.get_width()
                    #y = patch.get_y()
                    #ax.text(width + text_offset, y + bar_width/2,
                            #str(int(round(width, 0))) + u' €',
                            #color='black',ha='left', va='center')
                            ## bbox=dict(facecolor='white',
                            ## edgecolor='white', boxstyle="round"))
        #x_min, x_max = ax.get_xlim()
        #ax.set_xlim(x_min, x_max * 1.2)
        ## Ende Barlabels
        #ax.tick_params(axis='both', which='major', labelsize=9)
        #ax.set_yticks(y_pos)
        #ax.set_yticklabels(categories)
        #ax.set_title(self.title)
        #ax.set_xlabel(x_label)
        #ax.xaxis.set_major_formatter(mticker.FormatStrFormatter(u'%d €'))
        #ax.xaxis.grid(True, which='major')
        #box = ax.get_position()
        #ax.set_position([box.x0 + box.width * 0.2, box.y0,
                         #box.width * 0.8, box.height])
        #return ax


#class VergleichWEDiagramm(VergleichsDiagramm):
    #_column = 'WE_gesamt'
    #_type_of_use = Nutzungsart.WOHNEN
    #_unit = 'Wohneinheit'


#class VergleichAPDiagramm(VergleichsDiagramm):
    #_column = 'AP_gesamt'
    #_type_of_use = Nutzungsart.GEWERBE
    #_unit = 'Arbeitsplatz'

