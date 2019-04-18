from abc import ABC


class Output(ABC):
    '''
    abstract class for visual outputs of tools
    '''

    def draw(self):
        return NotImplemented


class Diagram(Output, ABC):
    '''
    abstract class for diagrams
    '''

    def draw(self):
        pass
