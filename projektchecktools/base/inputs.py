from abc import ABC
import os
from qgis.PyQt.Qt import (QSpinBox, QSlider, QObject, QDoubleSpinBox,
                          QLineEdit, QComboBox, Qt, QLabel, QHBoxLayout,
                          QCheckBox, QPushButton, QSizePolicy)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import pyqtSignal

from settings import settings


class InputType(QObject):
    '''
    abstract class for an input ui element
    '''
    changed = pyqtSignal(object)
    focus = pyqtSignal()

    def __init__(self, hide_in_overview=True):
        self.hide_in_overview = hide_in_overview
        self._input = None
        self._value = None
        super().__init__()

    def draw(self, layout, unit=''):
        self.layout = layout
        layout.addWidget(self.input)
        if unit:
            layout.addWidget(QLabel(unit))

    def create(self):
        raise NotImplementedError

    @property
    def input(self):
        if self._input:
            try:
                self._input.parent()
                return self._input
            except RuntimeError:
                pass
        self._input = self.create()
        self.registerFocusEvent(self._input)
        self.set_value(self._value)
        return self._input

    @property
    def value(self):
        if self._input:
            return self.get_value()
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        if self._input:
            self.set_value(value)

    def set_value(self, value):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError

    @property
    def locked(self):
        '''override function to implement a locked state'''
        return False

    def registerFocusEvent(self, input):
        # dirty but works, easier than subclassing all types of inputs just to
        # emit the signal
        focus_base = input.focusInEvent
        def focusInEvent(evt):
            focus_base(evt)
            self.focus.emit()
        input.focusInEvent = focusInEvent

    def remove(self):
        self.layout.removeWidget(self.input)


class Checkbox(InputType):
    '''
    checkbox input
    '''

    def create(self):
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self.changed.emit)
        return checkbox

    def set_value(self, checked):
        self.input.setChecked(checked or False)

    def get_value(self):
        return self.input.isChecked()


class Slider(InputType):
    '''
    slider input
    '''

    def __init__(self, minimum=0, maximum=100000000, step=1, width=300,
                 lockable=False, **kwargs):
        super().__init__(**kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.lockable = lockable
        self.width = width
        self.step = step

    def create(self):
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.minimum)
        self.slider.setMaximum(self.maximum)
        self.slider.setTickInterval(self.step)
        self.slider.setFixedWidth(self.width)
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(self.minimum)
        self.spinbox.setMaximum(self.maximum)
        self.spinbox.setSingleStep(self.step)
        self.registerFocusEvent(self.spinbox)

        if self.lockable:
            self.lock_button = QPushButton()
            self.lock_button.setCheckable(True)
            self.lock_button.setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Fixed)

            def toggle_icon():
                is_locked = self.lock_button.isChecked()
                fn = '20190619_iconset_mob_lock_locked_02.png' if is_locked \
                    else '20190619_iconset_mob_lock_unlocked_02.png'
                self.slider.setEnabled(not is_locked)
                self.spinbox.setEnabled(not is_locked)
                icon_path = os.path.join(settings.IMAGE_PATH, 'iconset_mob', fn)
                icon = QIcon(icon_path)
                self.lock_button.setIcon(icon)
            toggle_icon()
            self.lock_button.clicked.connect(toggle_icon)

        self.slider.valueChanged.connect(
            lambda: self.set_value(self.slider.value()))
        self.spinbox.valueChanged.connect(
            lambda: self.set_value(self.spinbox.value()))
        self.slider.valueChanged.connect(
            lambda: self.changed.emit(self.get_value()))
        self.spinbox.valueChanged.connect(
            lambda: self.changed.emit(self.get_value())
        )
        return self.slider

    def set_value(self, value):
        for element in [self.slider, self.spinbox]:
            # avoid infinite recursion
            element.blockSignals(True)
            element.setValue(value or 0)
            element.blockSignals(False)

    @property
    def locked(self):
        if not self.lockable:
            return False
        return self.lock_button.isChecked()

    def draw(self, layout, unit=''):
        self._input = self.create()
        l = QHBoxLayout()
        l.addWidget(self.slider)
        l.addWidget(self.spinbox)
        if unit:
            l.addWidget(QLabel(unit))
        if self.lockable:
            l.addWidget(self.lock_button)
        layout.addLayout(l)

    def get_value(self):
        return self.slider.value()


class ComboBox(InputType):
    def __init__(self, values=[], data=[], width=None, **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.values = values
        self.data = data

    def create(self):
        combobox = QComboBox()
        if self.width is not None:
            combobox.setFixedWidth(self.width)
        for i, value in enumerate(self.values):
            args = [value]
            if self.data:
                args.append(self.data[i])
            combobox.addItem(*args)
        combobox.currentIndexChanged.connect(
            lambda: self.changed.emit(self.get_value()))
        return combobox

    def set_value(self, value):
        self.input.setCurrentText(str(value))

    def get_value(self):
        return self.input.currentText()

    def get_data(self):
        return self.input.currentData()


class LineEdit(InputType):
    def __init__(self, width=None, **kwargs):
        super().__init__(**kwargs)
        self.width = width

    def create(self):
        line_edit = QLineEdit()
        if self.width is not None:
            line_edit.setFixedWidth(self.width)
        line_edit.textChanged.connect(self.changed.emit)
        return line_edit

    def set_value(self, value):
        self.input.setText(str(value or ''))

    def get_value(self):
        return self.input.text()


class SpinBox(InputType):
    InputClass = QSpinBox
    def __init__(self, minimum=0, maximum=100000000, step=1, **kwargs):
        super().__init__(**kwargs)
        self.minimum = minimum
        self.maximum = maximum
        self.step = step

    def create(self):
        spinbox = self.InputClass()
        spinbox.setMinimum(self.minimum)
        spinbox.setMaximum(self.maximum)
        spinbox.setSingleStep(self.step)
        spinbox.valueChanged.connect(self.changed.emit)
        return spinbox

    def set_value(self, value):
        self.input.setValue(value or 0)

    def get_value(self):
        return self.input.value()


class DoubleSpinBox(SpinBox):
    InputClass = QDoubleSpinBox
