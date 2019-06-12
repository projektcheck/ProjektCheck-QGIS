from abc import ABC
from qgis.PyQt.Qt import (QVBoxLayout, QHBoxLayout, QFrame, QObject,
                          QLabel)
from qgis.PyQt.QtWidgets import QSpacerItem, QSizePolicy
from typing import Union

from pctools.base import InputType


class Param:
    '''
    single parameter
    '''

    def __init__(self, value, input_type: InputType = None, label: str = ''):
        self.label = label
        self.input_type = input_type
        self.value = value

    def show(self, parent):
        layout = QHBoxLayout()
        label = QLabel(self.label)
        value_label = QLabel(str(self.value))
        layout.addWidget(label)
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(value_label)
        parent.addLayout(layout)


class Dependency(ABC):
    '''
    base class for dependencies between fields
    '''
    params = []


class Seperator:
    ''''''
    def show(self, parent):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        parent.addWidget(line)


class Title:
    ''''''
    def __init__(self, title):
        self.title = title

    def show(self, parent):
        label = QLabel(self.title)
        parent.addWidget(label)


class ParamView:
    '''
    holds grouped parameters
    '''
    def __init__(self):
        self.elements = []
        self.dependencies = []

    def add_dependency(self, dependency: Dependency):
        pass

    def add(self, element: Union[InputType, Seperator, Title]):
        self.elements.append(element)

    def load(self):
        pass

    def show(self, parent: QObject, *args):
        layout = QVBoxLayout()
        for element in self.elements:
            element.show(layout)
        parent.addLayout(layout, *args)

    def close(self):
        pass

    def show_dialog(self, parent, modal=True):
        pass

    def trigger(self):
        pass


class ParamCluster(ParamView):
    '''
    logical unit of params, that trigger sth if one of them is changed
    '''
    views = []

    def add(self, view):
        pass

    def trigger(self):
        pass


class SumDependency(Dependency):
    '''
    all dependent fields add up to a total value
    '''
    def __init__(self, fields, total):
        pass

