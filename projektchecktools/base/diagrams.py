from abc import ABC
from typing import List
import numpy as np
import matplotlib
from matplotlib.patches import Patch
import locale
matplotlib.use('ps')
locale.setlocale(locale.LC_ALL, '')
matplotlib.rcParams['axes.formatter.use_locale'] = True

import matplotlib.pyplot as plt
import os

from projektchecktools.base.project import settings
from projektchecktools.base.dialogs import DiagramDialog

stylesheet = os.path.join(settings.TEMPLATE_PATH, 'styles', 'pc.mplstyle')
plt.style.use(stylesheet)


class MatplotDiagram(ABC):
    '''
    superclass to plot diagrams with matplotlib into a dialog
    '''
    def __init__(self, **kwargs):
        '''
        Parameters
        ----------
        **kwargs
            any kind of keyword arguments that will be accessible in the
            create-function
        '''
        self.dialog = None
        self.kwargs = kwargs
        self.title = kwargs.get('title', '')

    def draw(self, offset_x: int = 0, offset_y: int = 0):
        '''
        show the created plot in current process or externally in own process

        Parameters
        ----------
        offset_x: int, optional
            offset the dialog position on the x-axis by this amount in pixels,
            defaults to no offset
        offset_y: int, optional
            offset the dialog position on the y-axis by this amount in pixels,
            defaults to no offset
        '''
        if not self.dialog:
            figure = self.create(**self.kwargs)
            self.dialog = DiagramDialog(figure, title=self.title)
        self.dialog.show(offset_x=offset_x, offset_y=offset_y)

    def create(self, **kwargs) -> 'Figure':
        '''
        to be implemented by subclasses,
        has to return the figure
        '''
        raise NotImplementedError


class BarChart(MatplotDiagram):
    '''
    a bar chart rendered with matplotlib
    '''
    def __init__(self, values: list, labels: List[str] = None,
                 colors: list = None, y_label: str = '', title: str = '',
                 show_legend: bool = True, custom_legend: dict = None):
        '''
        Parameters
        ----------
        values : list
            list of numeric values, one for each bar
        labels : list, optional
            list of labels, one for each bar, same length and order as 'values',
            defaults to no labels
        colors : list, optional
            list of strings or Color objects for the bars, same length and order
            as 'values', defaults to black bars
        y_label : str, optional
            label of the y-axis, defaults to no label
        title : str, optional
            title displayed above the diagram and used as dialog title, defaults
            to no title
        show_legend : bool, optional
            show a legend or not, defaults to showing the legend
        custom_legend : dict, optional
            a custom legend with labels as keys and colors as values, defaults
            to a generic legend
        '''
        super().__init__()
        self.values = values
        self.labels = labels or [''] * len(values)
        self.title = title
        self.colors = colors or ['b'] * len(values)
        self.y_label = y_label
        self.show_legend = show_legend
        self.custom_legend = custom_legend

    def create(self):
        '''
        override, create the bar chart figure
        '''
        x = np.arange(len(self.values))

        figure, ax = plt.subplots()
        width = 0.6
        bars = ax.bar(x, self.values, width, color=self.colors,
                      tick_label=self.labels)
        ax.set_title(self.title)
        plt.ylabel(self.y_label)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:n}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        va='bottom', ha='center')
        ax.get_yaxis().set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda y, p: f'{y:n}'))
        if self.show_legend:
            legend_elements = []
            if self.custom_legend:
                for label, color in self.custom_legend.items():
                    legend_elements.append(
                        Patch(facecolor=color, label=label))
            else:
                for i, label in enumerate(self.labels):
                    legend_elements.append(
                        Patch(facecolor=self.colors[i], label=label))
            ax.legend(handles=legend_elements, loc='best')
        figure.tight_layout()
        return figure


class PieChart(MatplotDiagram):
    '''
    a pie chart rendered with matplotlib
    '''
    def __init__(self, values, labels: List[str] = None, colors: list = None,
                 decimals: int = 1, title: str = '',
                 margin_left: int = 0.1, margin_top: int = 0.1,
                 margin_right: int = 0.1, margin_bottom: int = 0.2):
        '''
        Parameters
        ----------
        values : list
            list of numeric values, one for each section of the pie
        labels : list, optional
            list of labels, one for each section, same length and order as
            'values', defaults to no labels
        colors : list, optional
            list of strings or Color objects for the sections, same length and
            order as 'values', defaults to black bars
        title : str, optional
            title displayed above the diagram and used as dialog title, defaults
            to no title
        decimals : int, optional
            number of decimals of the values shown in the diagram, defaults to
            one decimal
        margin_left : int, optional
            left margin of the pie, defaults to 0.1
        margin_top : int, optional
            top margin of the pie, defaults to 0.1
        margin_right : int, optional
            right margin of the pie, defaults to 0.1
        margin_bottom : int, optional
            bottom margin of the pie, defaults to 0.2
        '''
        super().__init__()
        self.values = values
        self.labels = labels or [''] * len(values)
        self.title = title
        self.decimals = decimals
        self.colors = colors or plt.cm.Accent(
            np.linspace(0, 1, len(self.values)))
        self.margin_left = margin_left
        self.margin_top = margin_top
        self.margin_right = margin_right
        self.margin_bottom = margin_bottom

    def create(self):
        '''
        override, create the pie chart figure
        '''
        figure, ax = plt.subplots()
        ax.pie(self.values, labels=self.labels,
               autopct=f'%1.{self.decimals}f%%',
               startangle=90, colors=self.colors)
        ax.axis('equal')

        plt.figtext(.5, .92, self.title,
                    horizontalalignment='center',
                    fontsize=12)

        figure.subplots_adjust(bottom=self.margin_bottom, left=self.margin_left,
                               right=1-self.margin_right, top=1-self.margin_top)
        ax.legend(self.labels, loc='lower right', bbox_to_anchor=(1.1, -0.2))
        #figure.tight_layout()
        return figure