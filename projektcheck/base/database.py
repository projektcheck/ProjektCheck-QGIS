from abc import ABC
from typing import Union
import weakref


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
        self.geom = kwargs.pop('geom', None)
        self.table = table
        self._fields = []
        for f in table.fields():
            self._fields.append(f.name)
            v = kwargs.get(f.name, None)
            if v is None:
                v = f.default
            self.__dict__[f.name] = v

    #def __getattr__(self, k):
        #if k in self.__dict__['_fields']:
            #return self._values[k]
        #if k in self.__dict__:
            #return self.__dict__[k]
        #raise AttributeError(f'{k}')

    #def __setattr__(self, k, v):
        #if k in self._fields:
            #self._values[k] = v
        #self.__dict__[k] = v

    def save(self):
        kwargs = {f: getattr(self, f) for f in self._fields}
        if self.geom and hasattr(self.geom, 'isGeosValid') \
           and not self.geom.isGeosValid():
            self.geom = self.geom.makeValid()
        kwargs[self.table.geom_field] = self.geom
        if self.id is not None:
            self.table.set(self.id, **kwargs)
        else:
            row = self.table.add(**kwargs)
            self.id = row[self.table.id_field]

    def delete(self):
        self.table.delete(self.id)

    def __repr__(self):
        return f'Feature <{self.id}> of {self.table}'


class FeatureCollection:
    def __init__(self, table):
        self.table = table
        self._it = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._it >= len(self.table):
            self._it = 0
            self.table.reset_cursor()
            raise StopIteration
        else:
            row = next(self.table)
            self._it += 1
            return self._row_to_feature(row)

    def __len__(self):
        return len(self.table)

    def delete(self):
        ids = [feat.id for feat in self]
        for id in ids:
            self.table.delete(id)

    @property
    def workspace(self):
        return self.table.workspace

    def get(self, **kwargs):
        table = self.table.copy()
        prev_where = table.where
        table.filter(**kwargs)
        if len(table) > 1:
            raise ValueError('get returned more than one feature')
        if len(table) == 0:
            row = None
        else:
            row = self._row_to_feature(table[0])
        table.where = prev_where
        return row

    def add(self, **kwargs):
        if 'id' in kwargs:
            raise Exception("You can't set the id when adding a new feature. "
                            "The id will be assigned automatically.")
        feature = Feature(self.table, **kwargs)
        feature.save()
        return feature

    def fields(self):
        return self.table.fields()

    def add_field(self, field):
        self.table.add_field(field)

    def reset(self):
        self.table.reset()

    def filter(self, **kwargs):
        '''
        filtering django style
        supported: __in, __gt, __lt
        '''
        table = self.table.copy()
        table.filter(**kwargs)
        return FeatureCollection(table)

    def _row_to_feature(self, row):
        id = row.pop(self.table.id_field)
        geom = row.pop(self.table.geom_field)
        return Feature(table=self.table, id=id, geom=geom, **row)

    def __getitem__(self, idx):
        row = self.table[idx]
        return self._row_to_feature(row)

    def to_pandas(self):
        return self.table.to_pandas()

    def update_pandas(self, dataframe, **kwargs):
        self.table.update_pandas(dataframe, **kwargs)


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
        raise NotImplementedError

    @property
    def workspaces(self):
        raise NotImplementedError

    def get_workspace(self, name):
        raise NotImplementedError

    #def __repr__(self):
        #table_repr = '\n'.join(['   ' + str(v) for k, v in
                                #self.workspaces.items()])
        #return '{} {{\n{}\n}}'.format(type(self).__name__, table_repr)


class Workspace:
    '''
    abstract class for a workspace (e.g. file for file based dbs or
    scheme in sql)
    '''
    __refs__ = []

    def __init__(self, name: str, database: Database):
        self.name = name
        self.database = database
        self.__refs__.append(weakref.ref(self))

    def get_table(self, name):
        return self.database.get_table(name, self)

    @property
    def tables(self):
        raise NotImplementedError

    @classmethod
    def get_instances(cls):
        for inst_ref in cls.__refs__:
            inst = inst_ref()
            if inst is not None:
                yield inst


class Table(ABC):
    '''
    abstract class for a database table
    '''
    id_field = '__id__'
    geom_field = '__geom__'

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
        raise NotImplementedError

    @property
    def fields(self):
        '''
        override

        Returns
        -------
        row : list of str
            ordered field names (column names)
        '''
        raise NotImplementedError

    def features(self):
        '''
        override to cache features

        Returns
        -------
        features : FeatureCollection
        '''
        return FeatureCollection(self)

    def to_pandas(self):
        '''
        override

        Returns
        -------
        dataframe : Dataframe
            pandas dataframe with field names as column names containing all
            rows in table
        '''
        raise NotImplementedError

    def __len__(self):
        '''
        override

        Returns
        -------
        count : int
            number of rows (features)
        '''
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def create(self):
        raise NotImplementedError


class TemporaryTable(Table):
    '''
    temporary table with no database behind
    '''
