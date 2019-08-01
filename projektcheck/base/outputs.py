from abc import ABC


class Output(ABC):
    '''
    abstract class for visual outputs of tools
    '''

    def draw(self):
        raise NotImplementedError


class Diagram(Output, ABC):
    '''
    abstract class for diagrams
    '''

    def draw(self):
        pass
