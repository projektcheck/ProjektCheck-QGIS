from abc import ABC


class TableManager(ABC):
    ''''''

    def get_table(self):
        return NotImplemented

    def update_table(self):
        return NotImplemented


class Table(ABC):
    ''''''

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


class TemporaryTable(Table, ABC):
    ''''''

    def create(self):
        return NotImplemented
