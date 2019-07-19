from abc import ABC
from typing import Union

from projektcheck.utils.singleton import SingletonABCMeta


class Field:
    ''''''
    def __init__(self, name, type, default=None):
        self.name = name
        self.type = type
        self.default = default


class Feature:
    def __init__(self, table, fields, id=None):
        self.id = id
        self.fields = {}
        for field in fields:
            self.fields[field]
        self.fields = fields
        self.values = {}

    def __getattr__(self, k):
        if k in self.fields:
            return
        return self.__dict__[v]

    def save(self):
        pass

    def delete(self):
        #self._layer.DeleteFeature(id)
        pass


class FeatureCollection:
    def __init__(self, table, fields):
        self._table = table
        self.it = 0
        self.fields = fields

    def __iter__(self):
        self.it += 1
        return self

    def __next__(self):
        if self.it > self._table.count():
            self.it = 0
            raise StopIteration
        else:
            row = self._table.get_row(self.it)
            feature = 0

    def __len__(self):
        return len(self._table)

    def delete(self):
        pass

    def get(cls, **kwargs):
        #feat = self._layer.GetFeature(id)
        #feature = Feature(self, fields)
        #return feature
        pass

    def add(cls, project=None, **kwargs):
        #project = project or ProjectManager().active_project
        #table = cls.get_table(project=project)
        #fields = OrderedDict([
            #(k, f) for k, f in cls.__dict__.items() if isinstance(f, Field)
        #])
        #feature = Feature(table, fields)
        #return feature
        pass


    def filter(self, **kwargs):
        '''
        filtering django style
        supported: __in, __gt, __lt
        '''
        terms = []
        _prev = self._table.where
        for k, v in kwargs.items():
            if '__' not in k:
                if k not in self.fields:
                    raise ValueError(f'{k} not in fields')
                terms.append(f'{k} = {v}')
            elif k.endswith('__in'):
                vstr = [str(i) for i in v]
                terms.append(f'"{k.strip("__in")}" in ({",".join(vstr)})')
            elif k.endswith('__gt'):
                terms.append(f'"{k.strip("__gt")}" > {v}')
            elif k.endswith('__lt'):
                terms.append(f'"{k.strip("__lt")}" < {v}')
        where = ' and '.join(terms)
        if _prev:
            where = _prev + where
        table = self._table.__class__(where=where)


class Database(ABC):
    '''
    abstract class for managing connection to a database
    '''

    def __init__(self):
        pass

    def get_table(self, name: str, workspace: str = ''):
        '''
        Parameters
        ----------
        name : str
            table name
        workspace : str
            name of workspace (scheme or file), by default no workspace

        Returns
        -------
        table : Table

        '''
        return NotImplemented

    @property
    def workspaces(self):
        return NotImplemented

    def get_workspace(self, name):
        return NotImplemented

    #def __repr__(self):
        #table_repr = '\n'.join(['   ' + str(v) for k, v in
                                #self.workspaces.items()])
        #return '{} {{\n{}\n}}'.format(type(self).__name__, table_repr)


class Workspace:
    '''
    abstract class for a workspace (e.g. file for file based dbs or
    scheme in sql)
    '''
    def __init__(self, name: str, database: Database):
        self.name = name
        self.database = database

    def get_table(self, name):
        return self.database.get_table(name, self)

    @property
    def tables(self):
        return NotImplemented


class Table(ABC):
    '''
    abstract class for a database table
    '''

    def __init__(self, name: str, workspace: Union[Workspace, str] = None,
                 where=''):
        self.name = name
        self.workspace = workspace
        self.where = where

    def __iter__(self):
        return self

    def __next__(self):
        '''
        override for iterating rows

        Returns
        -------
        row : dict
            dictionary with field names as keys and values of fields as values
            representing the content of a single row
        '''
        return NotImplemented

    @property
    def fields(self):
        '''
        override

        Returns
        -------
        row : list of str
            ordered field names (column names)
        '''
        return NotImplemented

    @property
    def features(self):
        '''
        override to cache features

        Returns
        -------
        features : FeatureCollection
        '''
        return FeatureCollection(self)

    def as_pandas(self):
        '''
        override

        Returns
        -------
        dataframe : Dataframe
            pandas dataframe with field names as column names containing all
            rows in table
        '''
        return NotImplemented

    def count(self):
        '''
        override

        Returns
        -------
        count : int
            number of rows (features)
        '''
        return NotImplemented

    def update(self):
        return NotImplemented

    def create(self):
        return NotImplemented


class TemporaryTable(Table):
    '''
    temporary table with no database behind
    '''
