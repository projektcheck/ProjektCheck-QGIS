from abc import ABC
from typing import Union

from projektcheck.utils.singleton import SingletonABCMeta


class Field:
    ''''''
    def __init__(self, datatype, default=None, name=''):
        self.name = name
        self.datatype = datatype
        self.default = default

    def __repr__(self):
        return f'Field {self.name} {self.datatype}'


class Feature:
    def __init__(self, table, **kwargs):
        self.__dict__['_fields'] = {f.name: f for f in table.fields()}
        self.id = kwargs.pop('id', None)
        self._table = table
        self.geom = kwargs.pop('geom', None)
        self._values = {f.name: kwargs.get(f.name, None) or f.default
                        for f in table.fields()}

    def __getattr__(self, k):
        if k in self.__dict__:
            return self.__dict__[k]
        if k in self._fields:
            return self._values[k]
        raise AttributeError(f'{k}')

    def __setattr__(self, k, v):
        if k in self._fields:
            self._values[k] = v
        else:
            self.__dict__[k] = v

    def save(self):
        kwargs = self._values.copy()
        kwargs['geom'] = self.geom
        if self.id is not None:
            self._table.set(self.id, **kwargs)
        else:
            row = self._table.add(**kwargs)
            self.id = row[self._table.id_field]

    def delete(self):
        #self._layer.DeleteFeature(id)
        pass

    def __repr__(self):
        return f'Feature <{self.id}> of {self._table}'


class FeatureCollection:
    def __init__(self, table):
        self._table = table
        self._it = 0

    def __iter__(self):
        self._it += 1
        return self

    def __next__(self):
        if self._it > len(self._table):
            self._it = 0
            raise StopIteration
        else:
            row = next(self._table)
            id = row.pop(self._table.id_field)
            return Feature(table=self._table, id=id, **row)

    def __len__(self):
        return len(self._table)

    def delete(self):
        pass

    def get(self, id):
        row = self._table.get(id)
        row['id'] = id
        return Feature(self._table, **row)

    def add(self, **kwargs):
        if 'id' in kwargs:
            raise Exception("You can't set the id when adding a new feature. "
                            "The id will be assigned automatically.")
        feature = Feature(self._table, **kwargs)
        feature.save()
        return feature

    def filter(self, **kwargs):
        '''
        filtering django style
        supported: __in, __gt, __lt
        '''
        table = self._table.copy()
        table.filter(**kwargs)
        return FeatureCollection(table)


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
    id_field = '__id__'

    def __init__(self, name: str, workspace: Union[Workspace, str] = None,
                 field_names: list=None, where=''):
        self.name = name
        self.workspace = workspace
        self.where = where

    @property
    def where(self):
        return self._where

    @where.setter
    def where(self, value):
        self._where = value

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
            if id is available it has to be added as key {self.id_field}
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
