import os
from osgeo import ogr
import pandas as pd

from pctools.backend import Database, Table


class GeopackageTable(Table):
    def __init__(self, name, workspace, path):
        self.path = path
        self.workspace = workspace
        self.name = name

        self._conn = ogr.Open(path)
        self._layer = self._conn.GetLayerByName(name)

    def __next__(self):
        feature = self._layer.GetNextFeature()
        if not feature:
            raise StopIteration
        return feature.items()

    def fields(self):
        definition = self._layer.GetLayerDefn()
        fields = []
        for i in range(definition.GetFieldCount()):
            fields.append((definition.GetFieldDefn(i).GetName()))
        return fields

    def __iter__(self):
        return self

    def to_pandas(self):
        rows = []
        for row in self:
            rows.append(row.values())
        df = pd.DataFrame.from_records(rows, columns=self.fields())
        return df

    def count(self):
        return self._layer.GetFeatureCount()

    def __repr__(self):
        return f"GeopackageTable {self.name} {self.path}"


class Geopackage(Database):
    '''
    manages the connection to a geopackage db (file)
    '''
    def __init__(self, base_path: str = '', read_only: bool = False):
        super().__init__()
        self.base_path = base_path
        self.read_only = read_only

    def get_table(self, name: str, workspace: str = ''):
        path = os.path.join(self.base_path, workspace).rstrip('\\')
        if not os.path.exists(path) and not path.endswith('.gpkg'):
            path += '.gpkg'
        if not os.path.exists(path):
            raise FileNotFoundError(f'{path} does not exist')
        return GeopackageTable(name, workspace, path)

    def __repr__(self):
        return f"Geopackage {self.base_path}"
