from abc import ABC


class Output(ABC):
    ''''''

    def draw(self):
        return NotImplemented


class Diagram(Output, ABC):
    ''''''

    def draw(self):
        pass
