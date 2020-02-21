from abc import ABC
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
    superclass to plot diagrams with matplotlib
    '''
    def __init__(self, **kwargs):
        """
        title : str
        """
        self.dialog = None
        self.kwargs = kwargs
        self.title = kwargs.get('title', '')

    def draw(self, offset_x=0, offset_y=0):
        '''
        show the created plot in current process or externally in own process

        if not shown in external process, ArcMap will crash

        Parameters
        ----------
        external: bool, optional
            show the plot in an external process
            defaults to True
        '''
        if not self.dialog:
            figure = self.create(**self.kwargs)
            self.dialog = DiagramDialog(figure, title=self.title)
        self.dialog.show(offset_x=offset_x, offset_y=offset_y)

    def create(self, **kwargs):
        """to be implemented by subclasses,
        has to return the axes-object of the plot"""
        raise NotImplementedError


class BarChart(MatplotDiagram):
    def __init__(self, values, labels=None, colors=None, y_label='',
                 title='', show_legend=True, custom_legend=None):
        super().__init__()
        self.values = values
        self.labels = labels or [''] * len(values)
        self.title = title
        self.colors = colors or ['b'] * len(values)
        self.y_label = y_label
        self.show_legend = show_legend
        self.custom_legend = custom_legend

    def create(self):
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
    def __init__(self, values, labels=None, colors=None, decimals=1, title=''):
        super().__init__()
        self.values = values
        self.labels = labels or [''] * len(values)
        self.title = title
        self.decimals = decimals
        self.colors = colors or plt.cm.Accent(
            np.linspace(0, 1, len(self.values)))

    def create(self):
        figure, ax = plt.subplots()
        ax.pie(self.values, labels=self.labels,
               autopct=f'%1.{self.decimals}f%%',
               startangle=90, colors=self.colors)
        ax.axis('equal')

        plt.figtext(.5, .92, self.title,
                    horizontalalignment='center',
                    fontsize=12)

        ax.legend(self.labels, loc='best')

        return figure