from abc import ABC
from qgis.PyQt.Qt import QSpinBox, QSlider, QObject
from qgis.PyQt.QtCore import pyqtSignal


class InputType(QObject):
    '''
    abstract class for an input ui element
    '''
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()

    def draw(self, layout):
        return NotImplemented

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


class SpinBox(InputType):
    def __init__(self, minimum=0, maximum=100000000):
        super().__init__()
        self.minimum = minimum
        self.maximum = maximum
        self.input = QSpinBox()

    def set(self, value):
        self.input.setValue(value)

    def draw(self, layout):
        layout.addWidget(self.input)

    @property
    def value(self):
        return self.input.value()
