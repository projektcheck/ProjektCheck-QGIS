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

    def __init__(self, hide_in_overview=True):
        self.hide_in_overview = hide_in_overview
        super().__init__()

    def draw(self, layout):
        layout.addWidget(self.input)

    @property
    def value(self):
        return self.get_value()

    @value.setter
    def value(self, value):
        self.set_value(value)

    def set_value(self, value):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError

    @property
    def locked(self):
        '''override function to implement a locked state'''
        return False


class Checkbox(InputType):
    '''
    checkbox input
    '''
    def __init__(self, width=None):
        super().__init__()
        self.input = QCheckBox()
        self.input.stateChanged.connect(self.changed.emit)

    def set_value(self, checked):
        self.input.setChecked(checked or False)

    def get_value(self):
        return self.input.isChecked()


class Slider(InputType):
    '''
    slider input
    '''

    def __init__(self, minimum=0, maximum=100000000, step=1, width=300,
                 lockable=False):
        super().__init__()
        self.minimum = minimum
        self.maximum = maximum
        self.lockable = lockable
        self.step = step
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setTickInterval(step)
        self.slider.setFixedWidth(width)
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(minimum)
        self.spinbox.setMaximum(maximum)
        self.spinbox.setSingleStep(step)
        #self.spinbox.setFixedWidth(50)

        if lockable:
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

    def draw(self, layout):
        l = QHBoxLayout()
        l.addWidget(self.slider)
        l.addWidget(self.spinbox)
        if self.lockable:
            l.addWidget(self.lock_button)
        layout.addLayout(l)

    def get_value(self):
        return self.slider.value()


class ComboBox(InputType):
    def __init__(self, values=[], data=[], width=None):
        super().__init__()
        self.input = QComboBox()
        if width is not None:
            self.input.setFixedWidth(width)
        self.input.currentIndexChanged.connect(
            lambda: self.changed.emit(self.get_value()))
        for i, value in enumerate(values):
            args = [value]
            if data:
                args.append(data[i])
            self.add_value(*args)

    def add_value(self, value, data=None):
        self.input.addItem(value, userData=data)

    def set_value(self, value):
        self.input.setCurrentText(str(value))

    def get_value(self):
        return self.input.currentText()


class LineEdit(InputType):
    def __init__(self, width=None):
        super().__init__()
        self.input = QLineEdit()
        if width is not None:
            self.input.setFixedWidth(width)
        self.input.textChanged.connect(self.changed.emit)

    def set_value(self, value):
        self.input.setText(str(value or ''))

    def get_value(self):
        return self.input.text()


class SpinBox(InputType):
    InputClass = QSpinBox
    def __init__(self, minimum=0, maximum=100000000, step=1):
        super().__init__()
        self.minimum = minimum
        self.maximum = maximum
        self.input = self.InputClass()
        self.input.setMinimum(minimum)
        self.input.setMaximum(maximum)
        self.input.setSingleStep(step)
        self.input.valueChanged.connect(self.changed.emit)

    def set_value(self, value):
        self.input.setValue(value or 0)

    def get_value(self):
        return self.input.value()


class DoubleSpinBox(SpinBox):
    InputClass = QDoubleSpinBox
