from abc import ABC


class Param:
    '''
    single parameter
    '''

    def __init__(self, label: str, input_type, field, table):
        self.label = label
        self.input_type = input_type
        self.field = field
        self.table = table


class Dependency(ABC):
    '''
    base class for dependencies between fields
    '''
    params = []


class ParamView:
    '''
    holds grouped parameters
    '''
    def __init__(self, label: str):
        self.params = []
        self.dependencies = []
        self.label = label

    def add_dependency(self, dependency: Dependency):
        pass

    def add(self, param: Param):
        self.params.append(param)

    def load(self):
        pass

    def show(self, parent):
        pass

    def show_dialog(self, parent, modal=True):
        pass

    def trigger(self):
        pass


class ParamCluster(ParamView):
    '''
    logical unit of params, that trigger sth if one of them is changed
    '''
    views = []

    def add(self, view):
        pass

    def trigger(self):
        pass


class SumDependency(Dependency):
    '''
    all dependent fields add up to a total value
    '''
    def __init__(self, fields, total):
        pass

