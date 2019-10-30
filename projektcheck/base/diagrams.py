from abc import ABC
import subprocess
import matplotlib
matplotlib.use('ps')
import matplotlib.pyplot as plt
import os
import sys
import pickle

from projektcheck.utils import diagram_exec
from projektcheck.base.project import settings
from projektcheck.base.dialogs import DiagramDialog

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

    def draw(self):
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
        self.dialog.show()

    def create(self, **kwargs):
        """to be implemented by subclasses,
        has to return the axes-object of the plot"""
        raise NotImplementedError
