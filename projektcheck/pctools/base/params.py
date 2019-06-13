from abc import ABC
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.Qt import (QVBoxLayout, QHBoxLayout, QFrame, QObject,
                          QLabel)
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import QSpacerItem, QSizePolicy, QPushButton
from typing import Union
from collections import OrderedDict

from pctools.base import InputType, ParamsDialog


class Param(QObject):
    '''
    single parameter
    '''
    changed = pyqtSignal()

    def __init__(self, value, input_type: InputType = None, label: str = ''):
        super().__init__()
        self.label = label
        self.input_type = input_type
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.changed.emit()


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
    def __init__(self, title, fontsize=9):
        self.title = title
        self.fontsize = fontsize

    def show(self, parent):
        label = QLabel(self.title)
        font = QFont()
        font.setPointSize(self.fontsize)
        label.setFont(font)
        parent.addWidget(label)


class Params(QObject):
    '''
    holds grouped parameters
    '''
    confirmed = pyqtSignal()

    def __init__(self, parent: QObject = None):
        super().__init__()
        self._params = OrderedDict()
        self.elements = []
        self.dependencies = []
        self.parent = parent

    def add_dependency(self, dependency: Dependency):
        pass

    def add(self, element: Union[Param, Seperator, Title], name=''):
        self.elements.append(element)
        if name and isinstance(element, Param):
            self._params[name] = element

    @property
    def params(self):
        return self._params.values()

    def load(self):
        pass

    def show(self, *args):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        for element in self.elements:
            if isinstance(element, Param):
                row = QHBoxLayout()
                label = QLabel(element.label)
                value_label = QLabel(str(element.value))
                row.addWidget(label)
                row.addItem(
                    QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
                row.addWidget(value_label)
                layout.addLayout(row)
                element.changed.connect(lambda x, label=value_label:
                                        label.setText(str(element.value)))
            else:
                element.show(layout)

        row = QHBoxLayout()
        button = QPushButton('ändern')
        row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        row.addWidget(button)
        layout.addLayout(row)
        self.parent.addLayout(layout, *args)

        button.clicked.connect(self.show_dialog)

    def close(self):
        pass

    def show_dialog(self):
        dialog = ParamsDialog(self.params)
        dialog.show()
        self.confirmed.emit()

    def __getattr__(self, name):
        param = self._params.get(name, None)
        if param:
            return param
        return self.__dict__[name]

    def __setattr__(self, name, value):
        if isinstance(value, Param):
            self.add(value, name)
        else:
            self.__dict__[name] = value


class ParamCluster(Params):
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

