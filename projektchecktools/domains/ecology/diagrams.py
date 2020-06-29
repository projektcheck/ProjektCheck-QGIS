# -*- coding: utf-8 -*-
'''
***************************************************************************
    diagrams.py
    ---------------------
    Date                 : January 2020
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

diagrams showing results of calculations in the ecology domain
'''

__author__ = 'Christoph Franke'
__date__ = '17/01/2020'
__copyright__ = 'Copyright 2020, HafenCity University Hamburg'

import numpy as np
import matplotlib
import locale
matplotlib.use('agg')
import matplotlib.pyplot as plt

from projektchecktools.base.diagrams import MatplotDiagram


def horizontal_label_values(bars, ax, force_signum=False):
    '''
    place labels at bars of an axis
    '''
    for bar in bars:
        width = bar.get_width()
        r_format = '%.1f' if not force_signum else '%+.1f'
        val_label = locale.format_string(r_format, width)
        ha = 'right' if width < 0 else 'left'
        ax.annotate(
            ' ' + val_label if width > 0 else val_label,
            xy=(width if width >= 0 else width - 0.4,
                bar.get_y() + bar.get_height() / 2),
            va='center', ha=ha
        )

def u_categories(categories):
    ret = []
    prev = ''
    for category in categories:
        ret.append(category if category != prev else '')
        prev = category
    return ret


class Leistungskennwerte(MatplotDiagram):
    '''
    ratings of ground cover in status quo and prognosis as bar charts
    '''
    def create(self, **kwargs) -> 'Figure':
        '''
        Parameters
        ----------
        nullfall : list
            values for rating in status quo
        planfall : list
            values for rating in prognosis
        '''
        labels = kwargs['columns']

        y = np.arange(len(labels))
        width = 0.35  # the width of the bars

        figure, ax = plt.subplots()
        bars1 = ax.barh(y + width / 2 + 0.02, kwargs['nullfall'],
                         width, label='Nullfall', color='#fc9403')
        bars2 = ax.barh(y - width / 2 - 0.02, kwargs['planfall'],
                        width, label='Planfall', color='#036ffc')
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        #categories = u_categories(kwargs['categories'])
        #ax.minorticks_on()
        #ax.set_yticks(y, minor=True)
        #ax.set_yticks(np.arange(len(categories)), minor=False)
        #ax.set_yticklabels(labels, minor=True)
        #ax.set_yticklabels(categories, minor=False)
        #ax.tick_params(axis='y', which='major', pad=150, labelsize=12)

        ax.set_title(kwargs['title'])
        x_label = 'Bewertung'
        if 'max_rating' in kwargs:
            max_rating = kwargs['max_rating']
            ax.axes.set_xlim([0, max_rating + 1])
            x_label += f' (in Punkten von 0 bis {max_rating})'
        ax.set_xlabel(x_label)
        ax.set_xticks(range(0, max_rating + 1, 1))
        ax.get_xaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: f'{x:n}'))
        ax.legend(loc='best')

        horizontal_label_values(bars1, ax)
        horizontal_label_values(bars2, ax)

        figure.tight_layout()
        return figure


class LeistungskennwerteDelta(MatplotDiagram):
    '''
    difference of ratings of ground cover in prognosis to the ones in status quo
    as bar charts
    '''
    def create(self, **kwargs) -> 'Figure':
        '''
        Parameters
        ----------
        delta : list
            values of delta between rating in prognosis and status quo
        '''
        labels = kwargs['columns']

        y = np.arange(len(labels))
        data = kwargs['delta']

        figure, ax = plt.subplots()
        colors = np.full(len(data), 'g')
        colors[data < 0] = 'r'

        bars = ax.barh(y, data, align='center', color=colors)

        ax.set_yticks(y)
        #categories = u_categories(kwargs['categories'])
        #ax.minorticks_on()
        #ax.set_yticks(y, minor=True)
        #ax.set_yticks(np.arange(len(categories)), minor=False)
        #ax.set_yticklabels(labels, minor=True)
        #ax.set_yticklabels(categories, minor=False)
        #ax.tick_params(axis='y', which='major', pad=150, labelsize=12)

        ax.set_xlabel('Bewertung im Planfall minus Bewertung im Nullfall')
        ax.set_title(kwargs['title'])
        max_rating = kwargs.get('max_rating', 0)
        min_val = -max_rating or min(-3, min(data))
        max_val = max_rating or max(3, max(data))

        ax.set_xlim(left=min_val-1, right=max_val+1)
        ax.set_xticks(range(min_val, max_val+1, 1))
        ax.set_yticklabels(labels)
        ax.get_xaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(
                lambda x, p: locale.format_string('%+d', x)))
        ax.axvline(linewidth=1, color='grey')
        ax.legend()

        horizontal_label_values(bars, ax, force_signum=True)

        figure.tight_layout()
        return figure