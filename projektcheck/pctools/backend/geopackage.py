from pctools.backend import Database


class Geopackage(Database):
    '''
    manages the connection to a geopackage db (file)
    '''
    def __init__(self, base_path: str = ''):
        super().__init__()
        self.base_path = base_path

    def add_workspace(self, name, path, is_base: bool = True):
        workspace = super().add_workspace(name, path)
        workspace.is_base = is_base

#class GeopackageTable(Table):
    #'''
    #representation of a table in a geopackage
    #'''
