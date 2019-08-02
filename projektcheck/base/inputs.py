from abc import ABC
from qgis.PyQt.Qt import (QSpinBox, QSlider, QObject, QDoubleSpinBox,
                          QLineEdit, QComboBox, Qt, QLabel, QHBoxLayout)
from qgis.PyQt.QtCore import pyqtSignal


class InputType(QObject):
    '''
    abstract class for an input ui element
    '''
    changed = pyqtSignal()

    def __init__(self):
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


class Slider(InputType):
    '''
    slider input
    '''

    def __init__(self, minimum=0, maximum=100000000, step=1, width=300,
                 lockable=False):
        super().__init__()
        self.minimum = minimum
        self.maximum = maximum
        self.step = step
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.slider.setTickInterval(step)
        self.slider.setMinimumWidth(width)
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(minimum)
        self.spinbox.setMaximum(maximum)
        self.spinbox.setSingleStep(step)
        self.slider.valueChanged.connect(
            lambda: self.set_value(self.slider.value()))
        self.spinbox.valueChanged.connect(
            lambda: self.set_value(self.spinbox.value()))
        self.slider.valueChanged.connect(lambda: self.changed.emit())
        self.spinbox.valueChanged.connect(lambda: self.changed.emit())

    def set_value(self, value):
        for element in [self.slider, self.spinbox]:
            # avoid infinite recursion
            element.blockSignals(True)
            element.setValue(value)
            element.blockSignals(False)

    def draw(self, layout):
        l = QHBoxLayout()
        l.addWidget(self.slider)
        l.addWidget(self.spinbox)
        layout.addLayout(l)

    def get_value(self):
        return self.slider.value()


class ComboBox(InputType):
    def __init__(self, values):
        super().__init__()
        self.input = QComboBox()
        self.input.currentIndexChanged.connect(lambda: self.changed.emit())
        for value in values:
            self.input.addItem(value)

    def set_value(self, value):
        self.input.setCurrentText(str(value))

    def get_value(self):
        return self.input.currentText()


class LineEdit(InputType):
    def __init__(self):
        super().__init__()
        self.input = QLineEdit()
        self.input.textChanged.connect(lambda: self.changed.emit())

    def set_value(self, value):
        self.input.setText(str(value))

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
        self.input.valueChanged.connect(lambda: self.changed.emit())

    def set_value(self, value):
        self.input.setValue(value)

    def get_value(self):
        return self.input.value()


class DoubleSpinBox(SpinBox):
    InputClass = QDoubleSpinBox
