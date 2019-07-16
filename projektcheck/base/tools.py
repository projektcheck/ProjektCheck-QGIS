from abc import ABC


class Tool(ABC):
    '''
    abstract class for tools triggered by clicking a certain ui element
    '''

    def __init__(self, ui_element, params):
        self.ui_element = ui_element
        self.params = params

    def run(self):
        return NotImplemented

    def store(self):
        return NotImplemented


class CalculationTool(Tool, ABC):
    '''
    abstract class for calculations
    '''
    outputs = []


class DrawingTool(Tool, ABC):
    '''
    abstract class for tools drawing on the canvas
    '''

    def draw(self, canvas):
        return NotImplemented

    def load(self):
        return NotImplemented

    def run(self):
        pass


