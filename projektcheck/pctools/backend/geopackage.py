import os

from pctools.backend import Database, Table


class GeopackageTable(Table):
    def __init__(self, name, workspace, path):
        self.path = path
        self.workspace = workspace
        self.name = name


class Geopackage(Database):
    '''
    manages the connection to a geopackage db (file)
    '''
    def __init__(self, base_path: str = '', read_only: bool = False):
        super().__init__()
        self.base_path = base_path
        self.read_only = read_only

    def get_table(self, name: str, workspace: str):
        path = os.path.join(self.base_path, workspace)
        if not os.path.exists(path) and not path.endswith('.gpkg'):
            path += '.gpkg'
        if not os.path.exists(path):
            raise FileNotFoundError(f'{path} does not exist')
        return GeopackageTable(name, workspace, path)


#class GeopackageTable(Table):
    #'''
    #representation of a table in a geopackage
    #'''
