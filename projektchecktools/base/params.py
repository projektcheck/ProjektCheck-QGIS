from abc import ABC
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.Qt import (QVBoxLayout, QHBoxLayout, QFrame, QObject,
                          QLabel, QGridLayout, QDialogButtonBox, QWidget,
                          QScrollArea, QGroupBox)
from projektchecktools.utils.utils import clear_layout
from qgis.PyQt.QtGui import QIcon, QCursor
from qgis.PyQt.QtWidgets import (QSpacerItem, QSizePolicy,
                                 QPushButton, QLayoutItem)
from typing import Union
from collections import OrderedDict
import math
import os
import locale
locale.setlocale(locale.LC_ALL, '')
import json
import yaml

from projektchecktools.base.inputs import InputType
from projektchecktools.base.dialogs import Dialog

from settings import settings


class ClickableWidget(QWidget):
    clicked = pyqtSignal(object)
    def mousePressEvent(self, evt):
        self.clicked.emit(evt)


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
                 unit='', help_text='', repr_format=None, value_label=None):
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
        value_label : str, optional
            initial label of value shown in UI, defaults to
            representation of value
        '''
        super().__init__()
        self._value = value
        self.label = label
        self.input = input
        if self.input:
            self.input.value = value
        self.unit = unit
        self.repr_format = repr_format
        _repr = value_label if value_label is not None else self._v_repr(value)
        self._value_label = QLabel(_repr)
        self.help_text = help_text

    @property
    def is_locked(self):
        return self.input.is_locked

    @property
    def value(self):
        return self._value

    def _v_repr(self, value):
        if self.repr_format:
            return locale.format_string(self.repr_format, value)
        if isinstance(value, float):
            v_repr = locale.format_string("%.2f", value, grouping=True)
        elif isinstance(value, bool):
            v_repr = 'ja' if value == True else 'nein'
        elif isinstance(value, int):
            v_repr = f'{value:n}'
        elif value is None:
            v_repr = '-'
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
        self.row = QHBoxLayout()
        label = QLabel(self.label)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding)
        if isinstance(layout, QGridLayout):
            n_rows = layout.rowCount()
            layout.addWidget(label, n_rows, 0)
            layout.addItem(spacer, n_rows, 1)
            layout.addLayout(self.row, n_rows, 2)
        else:
            self.row.addWidget(label)
            self.row.addItem(spacer)
            layout.addLayout(self.row)
        if edit:
            self.input.draw(self.row, unit=self.unit)
        else:
            self.row.addWidget(self._value_label)
            if self.unit:
                unit_label = QLabel(self.unit)
                self.row.addWidget(unit_label)


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
                if param == p or p.is_locked:
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
    def __init__(self, title, fontsize=8, bold=True):
        self.title = title
        self.fontsize = fontsize
        self.bold = bold

    def draw(self, layout):
        '''
        draw title in given layout (appended)

        Parameters
        ----------
        layout : QBoxLayout
            layout to append the drawn parameter to
        '''
        label = QLabel(self.title)
        font = label.font()
        font.setBold(self.bold)
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
    HELP_PATH = os.path.join(settings.HELP_PATH, 'params')

    def __init__(self, parent: QObject = None,
                 button_label: str = 'Editieren', editable: bool = True,
                 help_text='', help_file=None):
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
        self.layout = QVBoxLayout()
        self.layout.setSpacing(5)
        self.help_dict = {
            'tooltip': 'Parameter editieren'
        }
        if help_file:
            self.help_file = help_file if os.path.exists(help_file) else \
                os.path.join(self.HELP_PATH, help_file)
            if os.path.exists(self.help_file):
                with open(self.help_file) as json_file:
                    self.help_dict = yaml.safe_load(json_file)
        # passed help text overrides the one from file
        if help_text or 'beschreibung' not in self.help_dict:
            self.help_dict['beschreibung'] = help_text

    def add(self, element: Union[Param, Seperator, Title, QLayoutItem],
            name=''):
        '''
        add an element (parameter or style element)
        elements will be rendered in order of addition

        '''
        self._elements.append(element)
        if name and isinstance(element, Param):
            self._params[name] = element
            if element.input:
                if element.help_text or name not in self.help_dict:
                    self.help_dict[name] = element.help_text
                else:
                    element.help_text = self.help_dict[name]

    @property
    def params(self):
        return self._params.values()

    def load(self):
        pass

    def show(self, *args, title='Parameter einstellen', scrollable=False):
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

        # Debug: function to automatically write a help file with all params
        # with empty texts, should be removed in production
        if (settings.DEBUG and getattr(self, 'help_file', None) and
            not os.path.exists(self.help_file)):
            if not os.path.exists(self.HELP_PATH):
                os.mkdir(self.HELP_PATH)
            with open(self.help_file, 'w') as json_file:
                json.dump(self.help_dict, json_file, indent=4)

        self.dialog = ParamsDialog(parent=None,
                                   help_text=self.help_dict['beschreibung'],
                                   title=title)

        self.parent.addLayout(self.layout, *args)

        if scrollable:
            frame = QFrame()
            scroll_area = QScrollArea()
            layout = QVBoxLayout()
            layout.setSpacing(5)
            frame.setLayout(layout)
            scroll_area.setWidget(frame)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFixedHeight(400)
            self.layout.addWidget(scroll_area)
        else:
            layout = self.layout

        for element in self._elements:
            if isinstance(element, QLayoutItem):
                layout.addItem(element)
            # overview
            elif not getattr(element, 'hide_in_overview', None):
                element.draw(layout)
            self.dialog.draw(element)


        if not self.editable:
            return

        row = QHBoxLayout()
        button = QPushButton(self.button_label)
        icon = QIcon(os.path.join(settings.IMAGE_PATH, 'iconset_mob',
                                  '20190619_iconset_mob_edit_1.png'))
        button.setIcon(icon)
        tool_tip = self.help_dict.get('tooltip', None)
        button.setToolTip(tool_tip)
        row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        row.addWidget(button)
        self.layout.addItem(
            QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Minimum))
        self.layout.addLayout(row)

        button.clicked.connect(self.show_dialog)

    def get(self, name):
        return self._params.get(name, None)

    def close(self):
        '''
        close rendered parameters
        '''
        if self.dialog:
            clear_layout(self.dialog.layout)
            del(self.dialog)
        clear_layout(self.layout)

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

    def __getitem__(self, key):
        return self._params.get(key, None)

    def __setitem__(self, key, value):
        self.add(value, key)


class ParamsDialog(Dialog):
    def __init__(self, parent=None, title='Parameter einstellen',
                 help_text=None, help_expanded=True):
        super().__init__(modal=True, parent=parent,
                         ui_file='parameter_dialog.ui',
                         title=title)
        self.layout = self.base_layout
        self.help_widget.setVisible(help_expanded)
        if help_text is None:
            self.details_button.setVisible(False)
        else:
            self.back_button.clicked.connect(
                lambda: self.show_help(help_text, hide_back=True, expand=True))
            self.show_help(help_text, hide_back=True)
        def toggle(checked):
            if checked:
                self.details_button.setText('Hilfe ausblenden <<')
            if not checked:
                self.adjustSize()
                self.details_button.setText('Hilfe anzeigen >>')
        self.details_button.toggled.connect(toggle)
        self.details_button.setChecked(help_expanded)
        self.back_button.setCursor(QCursor(Qt.PointingHandCursor))
        self._grid = None

    def exec_(self):
        min_width = self.base_layout.minimumSize().width() + 50
        self.param_widget.setMinimumWidth(min_width)
        min_height = self.base_layout.minimumSize().height()
        self.min_height = min(900, min_height + 100)
        self.param_widget.setMinimumHeight(self.min_height)
        return super().exec_()

    def draw(self, element):
        self.inputs = []
        # put param objects into grid, else added to the base layout
        if isinstance(element, Param):
            if not self._grid:
                self._grid = QGridLayout()
                self.layout.addLayout(self._grid)
            element.draw(self._grid, edit=True)
            if element.help_text:
                help_button = QPushButton('?')
                help_button.setMaximumWidth(20)
                help_button.setToolTip('Hilfe')
                help_button.setCursor(QCursor(Qt.PointingHandCursor))
                help_button.setFlat(True)
                font = help_button.font()
                font.setUnderline(True)
                font.setBold(True)
                help_button.setFont(font)
                help_button.clicked.connect(
                    lambda: self.show_help(element.help_text, expand=True))
                element.row.addWidget(help_button)
            if element.input:
                element.input.focus.connect(
                    lambda: self.show_help(element.help_text))
                self.inputs.append(element.input)
        else:
            self._grid = None
            if isinstance(element, QLayoutItem):
                self.layout.addItem(element)
            else:
                element.draw(self.layout)
        self.adjustSize()

    def show_help(self, text, hide_back=False, expand=False):
        if not text:
            return
        self.help_text_edit.setText(text)
        if expand:
            self.details_button.setChecked(True)
        self.back_button.setVisible(not hide_back)

    def close(self):
        for input in self.inputs:
            input.remove()
        super().close()


class ParamCluster(Params):
    '''
    logical unit of params, that trigger sth if one of them is changed
    '''
    views = []

    def add(self, view):
        pass

    def trigger(self):
        pass


