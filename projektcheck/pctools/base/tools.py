from abc import ABC


class Tool(ABC):
    ''''''

    def __init__(self, ui_element, params):
        self.ui_element = ui_element
        self.params = params

    def run(self):
        return NotImplemented

    def store(self):
        return NotImplemented


class CalculationTool(Tool, ABC):
    ''''''
    outputs = []


class DrawingTool(Tool, ABC):
    ''''''

    def draw(self, canvas):
        return NotImplemented

    def load(self):
        return NotImplemented

    def run(self):
        pass


