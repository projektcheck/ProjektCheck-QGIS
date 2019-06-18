from abc import ABC

from pctools.utils.singleton import SingletonABCMeta


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
            name of workspace (scheme or file)

        Returns
        -------
        table : Table

        '''
        return NotImplemented

    #def __repr__(self):
        #table_repr = '\n'.join(['   ' + str(v) for k, v in
                                #self._workspaces.items()])
        #return '{} {{\n{}\n}}'.format(type(self).__name__, table_repr)


#class Workspace:
    #def __init__(self, name: str, path, database: Database):
        #self.name = name
        #self.path = path
        #self.database = database

    #def get_table(self, name):
        #return self.database.get_table(name, self.name)

    #def __str__(self):
        #ret = '{} - {}'.format(self.name, self.path)
        #return ret


class Table(ABC):
    '''
    abstract class for a database table
    '''

    def __init__(self, name: str, workspace: str):
        self.name = name
        self.workspace = workspace

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

    def fields(self):
        '''
        override

        Returns
        -------
        row : list of str
            ordered field names (column names)
        '''
        return NotImplemented

    def to_pandas(self):
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
