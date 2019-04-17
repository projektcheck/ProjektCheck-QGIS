from abc import ABC


class InputType(ABC):
    '''
    abstract class for an input ui element
    '''

    def __init__(self):
        pass

    def draw(self, parent):
        return NotImplemented


class Slider(InputType):
    '''
    slider input
    '''

    def __init__(self, minimum, maximum, step):
        pass

    def draw(self, parent):
        pass