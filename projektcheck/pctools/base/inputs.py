from abc import ABC
from qgis.PyQt.Qt import (QSpinBox, QSlider, QObject, QDoubleSpinBox,
                          QLineEdit, QComboBox, Qt, QLabel, QHBoxLayout)
from qgis.PyQt.QtCore import pyqtSignal


class InputType(QObject):
    '''
    abstract class for an input ui element
    '''
    #changed = pyqtSignal()

    def __init__(self):
        super().__init__()

    def draw(self, layout):
        layout.addWidget(self.input)

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, value):
        self.set(value)

    def set(self, value):
        return NotImplemented

    def get(self):
        return NotImplemented


class Slider(InputType):
    '''
    slider input
    '''

    def __init__(self, minimum=0, maximum=100000000, step=1, width=300):
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
            lambda: self.spinbox.setValue(self.slider.value()))
        self.spinbox.valueChanged.connect(
            lambda: self.slider.setValue(self.spinbox.value()))

    def set(self, value):
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def draw(self, layout):
        l = QHBoxLayout()
        l.addWidget(self.slider)
        l.addWidget(self.spinbox)
        layout.addLayout(l)

    def get(self):
        return self.slider.value()


class ComboBox(InputType):
    def __init__(self, values):
        super().__init__()
        self.input = QComboBox()
        for value in values:
            self.input.addItem(value)

    def set(self, value):
        self.input.setCurrentText(str(value))

    def get(self):
        return self.input.currentText()


class LineEdit(InputType):
    def __init__(self):
        super().__init__()
        self.input = QLineEdit()

    def set(self, value):
        self.input.setText(str(value))

    def get(self):
        return self.input.text()


class SpinBox(InputType):
    InputClass = QSpinBox
    def __init__(self, minimum=0, maximum=100000000, step=1):
        super().__init__()
        self.input = self.InputClass()
        self.input.setMinimum(minimum)
        self.input.setMaximum(maximum)
        self.input.setSingleStep(step)

    def set(self, value):
        self.input.setValue(value)

    def get(self):
        return self.input.value()


class DoubleSpinBox(SpinBox):
    InputClass = QDoubleSpinBox
