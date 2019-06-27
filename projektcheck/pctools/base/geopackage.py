import os
from osgeo import ogr
import pandas as pd
from typing import Union

from pctools.base import Database, Table, Workspace


class GeopackageWorkspace(Workspace):
    def __init__(self, name, database):
        self.name = name
        self.path = os.path.join(database.base_path, name).rstrip('\\')
        if not os.path.exists(self.path) and not self.path.endswith('.gpkg'):
            self.path += '.gpkg'
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'{self.path} does not exist')
        self._conn = ogr.Open(self.path, 0 if database.read_only else 1)

    @property
    def tables(self):
        tables = [l.GetName() for l in self._conn]
        return tables

    def get_table(self, name):
        return GeopackageTable(name, self)

    def __repr__(self):
        return f"GeopackageWorkspace {self.name} {self.path}"


class GeopackageTable(Table):
    def __init__(self, name, workspace: GeopackageWorkspace, where=''):
        self.workspace = workspace
        self.name = name
        self.where = where

    def __next__(self):
        self._cursor = self._layer.GetNextFeature()
        if not self._cursor:
            raise StopIteration
        return self._cursor.items()

    @property
    def where(self):
        return self._where

    @where.setter
    def where(self, value):
        self._cursor = None
        self._where = value
        self._layer = self.workspace._conn.GetLayerByName(self.name)
        self._layer.SetAttributeFilter(value)

    @property
    def fields(self):
        definition = self._layer.GetLayerDefn()
        fields = []
        for i in range(definition.GetFieldCount()):
            fields.append((definition.GetFieldDefn(i).GetName()))
        return fields

    def add(self, row: Union[dict, list]):
        if isinstance(row, list):
            row = dict(zip(self.fields, row))
        feature = ogr.Feature(self._layer.GetLayerDefn())
        for field, value in row.items():
            feature.SetField(field, value)
        self._layer.CreateFeature(feature)

    def delete(self, where=''):
        '''warning: resets cursor'''
        prev_where = self._where
        self.where = where
        i = 0
        for feature in self._layer:
            self._layer.DeleteFeature(feature.GetFID())
            i += 1
        self.where = prev_where
        return i

    def update_cursor(self, row: Union[dict, list]):
        if isinstance(row, list):
            row = dict(zip(self.fields, row))
        for field, value in row.items():
            self._cursor.SetField(field, value)
            self._layer.SetFeature(self._cursor)

    def to_pandas(self):
        rows = []
        for row in self:
            rows.append(row.values())
        df = pd.DataFrame.from_records(rows, columns=self.fields)
        return df

    @property
    def count(self):
        return self._layer.GetFeatureCount()

    def __repr__(self):
        return f"GeopackageTable {self.name} {self._layer}"


class Geopackage(Database):
    '''
    manages the connection to a geopackage db (file)
    '''
    def __init__(self, base_path: str = '.', read_only: bool = False):
        super().__init__()
        self.base_path = base_path
        self.read_only = read_only

    def get_table(self, name: str, workspace: str = ''):
        if not workspace:
            raise Exception('Geopackage backend does not support '
                            'tables without workspaces')
        return self.get_workspace(workspace).get_table(name)

    def get_workspace(self, name):
        return GeopackageWorkspace(name, self)

    @property
    def workspaces(self):
        workspaces = [f.rstrip('.gpkg') for f in os.listdir(self.base_path)
                      if os.path.isfile(os.path.join(self.base_path, f)) and
                      f.endswith('.gpkg')]
        return workspaces

    def __repr__(self):
        return f"Geopackage {self.base_path}"
