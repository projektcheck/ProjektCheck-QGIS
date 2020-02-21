from abc import ABC
import numpy as np
import matplotlib
from cycler import cycler
matplotlib.use('ps')
#matplotlib.rcParams['axes.prop_cycle'] = cycler(color='bgrcmyk')
#matplotlib.style.use('classic')
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
                 title=''):
        super().__init__()
        self.values = values
        self.labels = labels or [''] * len(values)
        self.title = title
        self.colors = colors
        self.y_label = y_label

    def create(self):
        x = np.arange(len(self.values))

        figure, ax = plt.subplots()
        width = 0.6
        bars = ax.bar(x, self.values, width, color=self.colors)
        ax.set_title(self.title)
        plt.xticks(x, self.labels)
        plt.ylabel(self.y_label)

        for bar in bars:
            height = bar.get_height()
            ax.annotate('{}'.format(height),
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        va='bottom')

        #ax.set_color_cycle(['kbkykrkg'])
        #ax.set_xticks(self.labels)

        #figure.tight_layout()
        return figure


class PieChart(MatplotDiagram):
    def __init__(self, values, labels=None, colors=None, title=''):
        super().__init__()
        self.values = values
        self.labels = labels or [''] * len(values)
        self.title = title
        self.colors = colors or plt.cm.Accent(
            np.linspace(0, 1, len(self.values)))

    def create(self):
        figure, ax = plt.subplots()
        ax.pie(self.values, labels=self.labels, autopct='%1.1f%%',
               startangle=90, colors=self.colors)
        ax.axis('equal')

        plt.figtext(.5, .92, self.title,
                    horizontalalignment='center',
                    fontsize=12)

        ax.legend(self.labels, loc='upper left',
                  bbox_to_anchor=(0.7, 0.1))

        return figure