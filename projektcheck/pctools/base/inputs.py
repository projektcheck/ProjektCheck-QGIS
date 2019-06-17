from abc import ABC
from qgis.PyQt.Qt import (QSpinBox, QSlider, QObject, QDoubleSpinBox,
                          QLineEdit, QComboBox)
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
        return NotImplemented


#class Slider(InputType):
    #'''
    #slider input
    #'''

    #def __init__(self, minimum=0, maximum=100000000, step=1):
        #super().__init__()
        #self.minimum = minimum
        #self.maximum = maximum
        #self.step = step

    #def draw(self, layout):
        #input = QSlider()
        #layout.addWidget(input)


class ComboBox(InputType):
    def __init__(self, values):
        super().__init__()
        self.input = QComboBox()
        for value in values:
            self.input.addItem(value)

    def set(self, value):
        self.input.setCurrentText(str(value))

    @property
    def value(self):
        return self.input.currentText()


class LineEdit(InputType):
    def __init__(self):
        super().__init__()
        self.input = QLineEdit()

    def set(self, value):
        self.input.setText(str(value))

    @property
    def value(self):
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

    @property
    def value(self):
        return self.input.value()


class DoubleSpinBox(SpinBox):
    InputClass = QDoubleSpinBox
