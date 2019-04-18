from abc import ABC


class Database(ABC):
    '''
    abstract class for managing connection to a database
    '''

    def get_table(self):
        return NotImplemented

    def update_table(self):
        return NotImplemented


class Table(ABC):
    '''
    abstract class for a database table
    '''

    def get(self):
        return NotImplemented

    def update_table(self):
        return NotImplemented

    def to_pandas(self):
        return NotImplemented

    def __iter__(self):
        # return the rows here
        return NotImplemented

    def __next__(self):
        return NotImplemented

    def create(self):
        return NotImplemented


class TemporaryTable(Table):
    '''
    temporary table with no database behind
    '''
