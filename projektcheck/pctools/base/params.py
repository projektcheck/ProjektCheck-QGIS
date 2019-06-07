from abc import ABC


class Params:
    '''
    holds grouped parameters
    '''
    def __init__(self, workspace, table, label=''):
        self.fields = []
        self.dependencies = []
        self.label = label
        self.workspace = workspace
        self.table = table

    def add_dependency(self, dependency):
        pass

    def add(self, field):
        pass

    def load(self):
        pass

    def show(self, parent):
        pass

    def show_dialog(self, parent, modal=True):
        pass

    def trigger(self):
        pass


class ParamCluster(Params):
    '''
    logical unit of params, that trigger sth if one of them is changed
    '''
    params = []

    def add(self, params):
        pass

    def trigger(self):
        pass


class Dependency(ABC):
    '''
    base class for dependencies between fields
    '''
    fields = []


class ParamField(Params):
    '''
    single parameter
    '''

    def __init__(self, label, input_type, field):
        pass


class SumDependency(Dependency):
    '''
    all dependent fields add up to a total value
    '''
    def __init__(self, fields, total):
        pass

