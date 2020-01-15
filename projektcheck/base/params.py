from abc import ABC
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.Qt import (QVBoxLayout, QHBoxLayout, QFrame, QObject,
                          QLabel)
from qgis.PyQt.QtGui import QFont, QIcon
from qgis.PyQt.QtWidgets import (QSpacerItem, QSizePolicy,
                                 QPushButton, QLayoutItem)
from typing import Union
from collections import OrderedDict
import math
import os
import locale
locale.setlocale(locale.LC_ALL, '')

from projektcheck.base.inputs import InputType
from projektcheck.base.dialogs import Dialog
from projektcheck.base.project import settings


class Param(QObject):
    '''
    single parameter for setting up domain calculations

    Attributes
    ----------
    value : basic_type
        current value of the parameter
    changed : pyqtSignal
        fired on change of value
    '''
    changed = pyqtSignal(object)

    def __init__(self, value, input: InputType = None, label: str = '',
                 unit=''):
        '''
        Parameters
        ----------
        value : basic_type
            initial value of parameter
        input : InputType, optional
            input for changing the value in the UI, not settable
            (and not viewed) in the UI if None
        label : str, optional
            label shown when parameter is drawn in UI
        '''
        super().__init__()
        self._value = value
        self.label = label
        self.input = input
        if self.input:
            self.input.value = value
        self.unit = unit
        self._value_label = QLabel(self._v_repr(value))

    @property
    def locked(self):
        return self.input.locked

    @property
    def value(self):
        return self._value

    def _v_repr(self, value):
        if isinstance(value, float):
            v_repr = locale.str(value)
        elif value is None:
            v_repr = '-'
        elif isinstance(value, bool):
            v_repr = 'ja' if value == True else 'nein'
        else:
            v_repr = str(value)
        return v_repr

    @value.setter
    def value(self, value):
        self._value = value
        self._value_label.setText(self._v_repr(value))
        if self.input:
            self.input.value = value
        self.changed.emit(value)

    def draw(self, layout, edit=False):
        '''
        draw parameter in given layout

        Parameters
        ----------
        layout : QBoxLayout
            layout to append the drawn parameter to
        edit : bool, optional
            edit mode displaying the label and input of parameter if True,
            else label and (uneditable) value, by default False
        '''
        if edit and not self.input:
            return
        row = QHBoxLayout()
        label = QLabel(self.label)
        row.addWidget(label)
        row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding))
        if edit:
            self.input.draw(row)
        else:
            row.addWidget(self._value_label)
        if self.unit:
            unit_label = QLabel(self.unit)
            row.addWidget(unit_label)
        layout.addLayout(row)


class Dependency(ABC):
    '''
    base class for dependencies between fields
    '''
    def __init__(self, params=[]):
        self._params = []
        for param in params:
            self.add(param)

    def add(self, param):
        param.input.changed.connect(lambda: self.on_change(param))
        self._params.append(param)

    def on_change(self, param):
        raise NotImplementedError


class SumDependency(Dependency):
    '''
    all dependent fields add up to a total value
    '''
    def __init__(self, total, params=[], decimals=0):
        super().__init__(params=params)
        self.total = total
        self.decimals = decimals

    def on_change(self, param):

        def distribute(value, equally=True):
            '''distribute given value to other (excl. the one currently changed)
            parameters which are not locked'''
            share = round(dif / (len(self._params) - 1), self.decimals)
            if equally:
                # equal share has to be different from zero (at least +-x.xxx1)
                share = math.copysign(
                    max(abs(share), 1/math.pow(10, self.decimals)), share)
            distributed = 0
            for p in self._params:
                if param == p or p.locked:
                    continue
                # no equal share -> try to add complete missing amount
                if not equally:
                    share = value - distributed
                current = p.input.value
                if current + share < p.input.minimum:
                    new_val = p.input.minimum
                elif current + share > p.input.maximum:
                    new_val = p.input.maximum
                else:
                    new_val = current + share
                delta = new_val - current
                p.input.value = new_val
                distributed += delta
                if abs(distributed) >= abs(dif):
                    break

        current_total = sum(p.input.value for p in self._params)
        dif = self.total - current_total
        # equal distribution of difference to target total
        distribute(dif)

        # set value of currently changed param to exact difference
        other_values = sum(p.input.value for p in self._params if p != param)
        print(other_values)
        param.input.value = self.total - other_values

        # change order for next time, so that another input is raised first
        # ToDo: can hit param currently changed, then same input is changed
        # again next round
        self._params.append(self._params.pop(0))


class Seperator:

    def __init__(self, margin=3):
        self.margin = margin

    '''
    seperator appendable to ui layout
    '''
    def draw(self, layout):
        '''
        draw seperator in given layout (appended)

        Parameters
        ----------
        layout : QBoxLayout
            layout to append the drawn parameter to
        '''
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        if self.margin:
            layout.addItem(QSpacerItem(0, self.margin, QSizePolicy.Fixed,
                                       QSizePolicy.Minimum))
        layout.addWidget(line)
        if self.margin:
            layout.addItem(QSpacerItem(0, self.margin, QSizePolicy.Fixed,
                                       QSizePolicy.Minimum))


class Title:
    '''
    title label appendable to ui layout
    '''
    def __init__(self, title, fontsize=9):
        self.title = title
        self.fontsize = fontsize

    def draw(self, layout):
        '''
        draw title in given layout (appended)

        Parameters
        ----------
        layout : QBoxLayout
            layout to append the drawn parameter to
        '''
        label = QLabel(self.title)
        font = QFont()
        font.setPointSize(self.fontsize)
        label.setFont(font)
        layout.addWidget(label)


class Params(QObject):
    '''
    collection of parameters, single parameters can be added by setting
    them as attributes

    Attributes
    ----------
    changed : pyqtSignal
        fired on change of any parameter in collection
    '''
    changed = pyqtSignal()

    def __init__(self, parent: QObject = None,
                 button_label: str = 'Editieren', editable: bool = True):
        '''
        Parameters
        ----------
        parent : QObject, optional
            ui element to draw the parameters in, can't be drawn if parent is
            None
        '''
        super().__init__()
        self._params = OrderedDict()
        self._elements = []
        self.button_label = button_label
        #self._dependencies = []
        self.parent = parent
        self.dialog = None
        self.editable = editable

    #def add_dependency(self, dependency: Dependency):
        #self._dependencies.append(dependency)
        #for param in self._params.values():
            #dependency.add_param(param)

    def add(self, element: Union[Param, Seperator, Title, QLayoutItem],
            name=''):
        '''
        add an element (parameter or style element)
        elements will be rendered in order of addition

        '''
        self._elements.append(element)
        if name and isinstance(element, Param):
            self._params[name] = element
            #for dependency in self._dependencies:
                #dependency.add(element)

    @property
    def params(self):
        return self._params.values()

    def load(self):
        pass

    def show(self, *args):
        '''
        render parameters and elements in parent

        Parameters
        ----------
        args : optional
            arguments for appending parameter layout to parent
            (like x, y if parent is grid layout)
        '''
        if self.parent is None:
            raise Exception("can't render Params object with no parent set")
        self.dialog = Dialog('parameter_dialog.ui', modal=True)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(5)

        def init_param_row(param):
            row = QHBoxLayout()
            label = QLabel(element.label)
            row.addWidget(label)
            row.addItem(
                QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
            return row

        for element in self._elements:
            if isinstance(element, QLayoutItem):
                self.layout.addItem(element)
                self.dialog.param_layout.addItem(element)
                continue
            # overview
            if not getattr(element, 'hide_in_overview', None):
                element.draw(self.layout)
            # dialog
            if isinstance(element, Param):
                element.draw(self.dialog.param_layout, edit=True)
            else:
                element.draw(self.dialog.param_layout)

        self.parent.addLayout(self.layout, *args)

        if not self.editable:
            return

        row = QHBoxLayout()
        button = QPushButton(self.button_label)
        icon = QIcon(os.path.join(settings.IMAGE_PATH, 'iconset_mob',
                                  '20190619_iconset_mob_edit_1.png'))
        button.setIcon(icon)
        row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        row.addWidget(button)
        self.layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.layout.addLayout(row)

        button.clicked.connect(self.show_dialog)

    def close(self):
        '''
        close rendered parameters
        '''
        if self.dialog:
            del(self.dialog)

    def show_dialog(self):
        '''
        show the dialog to edit parameters
        '''
        confirmed = self.dialog.exec_()
        if confirmed:
            has_changed = False
            for param in self.params:
                if not param.input or param.value == param.input.value:
                    continue
                param.value = param.input.value
                has_changed = True
            if has_changed:
                self.changed.emit()
        else:
            # reset inputs
            for param in self.params:
                if param.input:
                    param.input.value = param.value

    def __getattr__(self, name):
        param = self._params.get(name, None)
        if param:
            return param
        return self.__dict__.get(name, None)

    def __setattr__(self, name, value):
        if isinstance(value, Param):
            self.add(value, name)
        else:
            self.__dict__[name] = value

    def get(self, name):
        return self._params.get(name, None)

    def __getitem__(self, key):
        return self._params.get(key, None)

    def __setitem__(self, key, value):
        self.add(value, key)


class ParamCluster(Params):
    '''
    logical unit of params, that trigger sth if one of them is changed
    '''
    views = []

    def add(self, view):
        pass

    def trigger(self):
        pass


