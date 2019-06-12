from abc import ABC
from qgis.PyQt.Qt import QSpinBox, QSlider


class InputType(ABC):
    '''
    abstract class for an input ui element
    '''

    def __init__(self):
        pass

    def draw(self, parent):
        return NotImplemented

    @property
    def value(self):
        return NotImplemented


class Slider(InputType):
    '''
    slider input
    '''

    def __init__(self, minimum=0, maximum=100000000, step=1):
        self.minimum = minimum
        self.maximum = maximum
        self.step = step

    def draw(self, parent):
        input_el = QSlider()


class SpinBox(InputType):
    def __init__(self, minimum=0, maximum=100000000):
        self.minimum = minimum
        self.maximum = maximum

    def draw(self, parent):
        input_el = QSpinBox()
