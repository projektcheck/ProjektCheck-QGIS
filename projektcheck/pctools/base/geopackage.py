import os
from osgeo import ogr
from qgis.core import QgsGeometry
import pandas as pd
import numpy as np
from typing import Union
from collections import OrderedDict

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

    def get_table(self, name, where='', fields=None):
        if name not in self.tables:
            raise ValueError(f'layer {self.name} not found')
        return GeopackageTable(name, self, where=where, fields=fields)

    def __repr__(self):
        return f"GeopackageWorkspace {self.name} {self.path}"


class GeopackageTable(Table):
    def __init__(self, name, workspace: GeopackageWorkspace, where='',
                 fields=None):
        self.workspace = workspace
        self.name = name
        self.where = where
        self._fields = None
        if fields is not None:
            f = np.array(fields)
            isin = np.isin(f, np.array(self.fields))
            if not np.all(isin):
                notin = ', '.join(f[isin != True])
                raise ValueError(
                    f'fields "{notin}" are not in table {self.name}')
            self._fields = fields

    def __next__(self):
        cursor = self._layer.GetNextFeature()
        self._cursor = cursor
        if not cursor:
            raise StopIteration
        if self._fields is not None:
            items = OrderedDict([(f, cursor[f]) for f in self._fields])
        else:
            items = OrderedDict(self._cursor.items())
        return items

    @property
    def where(self):
        return self._where

    @where.setter
    def where(self, value):
        self._cursor = None
        self._where = value
        self._layer = self.workspace._conn.GetLayerByName(self.name)
        if self._layer is None:
            raise ConnectionError(f'layer {self.name} not found')
        self._layer.SetAttributeFilter(value)

    @property
    def fields(self):
        if self._fields is not None:
            return self._fields
        definition = self._layer.GetLayerDefn()
        fields = []
        for i in range(definition.GetFieldCount()):
            fields.append((definition.GetFieldDefn(i).GetName()))
        return fields

    def add(self, row: Union[dict, list], geom=None):
        if isinstance(row, list):
            fields = self._fields if self._fields is not None else self.fields
            row = dict(zip(fields, row))
        feature = ogr.Feature(self._layer.GetLayerDefn())
        for field, value in row.items():
            feature.SetField(field, value)
        if geom and isinstance(geom, QgsGeometry):
            geom = ogr.CreateGeometryFromWkt(geom.asWkt())
        if geom:
            feature.SetGeometry(geom)
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

    def as_pandas(self):
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

    def get_table(self, name: str, workspace: str = '', fields=None, where=''):
        if not workspace:
            raise Exception('Geopackage backend does not support '
                            'tables without workspaces')
        return self.get_workspace(workspace).get_table(
            name, where=where, fields=fields)

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
