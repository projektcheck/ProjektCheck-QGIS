# -*- coding: utf-8 -*-
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.ticker as mticker
import pandas as pd
import matplotlib.pyplot as plt

from projektchecktools.base.diagrams import MatplotDiagram


def horizontal_label_values(bars, ax):
    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            '{}'.format(width),
            xy=(width if width >= 0 else width - 0.4,
                bar.get_y() + bar.get_height() / 2),
            va='center'#, ha='left'
        )

def u_categories(categories):
    ret = []
    prev = ''
    for category in categories:
        ret.append(category if category != prev else '')
        prev = category
    return ret


class Leistungskennwerte(MatplotDiagram):
    def create(self, **kwargs):
        categories = u_categories(kwargs['categories'])
        labels = kwargs['columns']

        y = np.arange(len(labels))
        width = 0.35  # the width of the bars

        figure, ax = plt.subplots()
        bars1 = ax.barh(y + width / 2 + 0.02, kwargs['nullfall'],
                         width, label='Nullfall', color='#fc9403')
        bars2 = ax.barh(y - width / 2 - 0.02, kwargs['planfall'],
                        width, label='Planfall', color='#036ffc')

        ax.minorticks_on()
        ax.set_yticks(y, minor=True)
        ax.set_yticks(np.arange(len(categories)), minor=False)
        ax.set_yticklabels(labels, minor=True)
        ax.set_yticklabels(categories, minor=False)
        ax.tick_params(axis='y', which='major', pad=150, labelsize=12)

        ax.set_title(kwargs['title'])
        x_label = 'Bewertung'
        if 'max_rating' in kwargs:
            max_rating = kwargs['max_rating']
            ax.axes.set_xlim([0, max_rating])
            x_label += f' (in Punkten von 0 bis {max_rating})'
        ax.set_xlabel(x_label)
        ax.set_xticks(range(0, max_rating, 2))
        ax.get_xaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: f'{x:n}'))
        ax.legend(loc='best')

        horizontal_label_values(bars1, ax)
        horizontal_label_values(bars2, ax)

        figure.tight_layout()
        return figure


class LeistungskennwerteDelta(MatplotDiagram):
    def create(self, **kwargs):
        categories = u_categories(kwargs['categories'])
        labels = kwargs['columns']

        y = np.arange(len(labels))
        data = kwargs['delta']

        figure, ax = plt.subplots()
        colors = np.full(len(data), 'g')
        colors[data < 0] = 'r'

        bars = ax.barh(y, data, align='center', color=colors)

        ax.set_yticks(y)
        #ax.minorticks_on()
        #ax.set_yticks(y, minor=True)
        #ax.set_yticks(np.arange(len(categories)), minor=False)
        #ax.set_yticklabels(labels, minor=True)
        #ax.set_yticklabels(categories, minor=False)
        #ax.tick_params(axis='y', which='major', pad=150, labelsize=12)

        ax.set_xlabel('Bewertung im Planfall minus Bewertung im Nullfall')
        ax.set_title(kwargs['title'])
        min_val = min(-3, min(data))
        max_val = max(3, max(data))
        ax.set_xlim(left=min_val, right=max_val)
        ax.set_xticks(range(min_val, max_val, 2))
        ax.set_yticklabels(labels)
        ax.get_xaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, p: f'{x:n}'))
        ax.axvline(linewidth=1, color='grey')
        ax.legend()

        horizontal_label_values(bars, ax)

        figure.tight_layout()
        return figure