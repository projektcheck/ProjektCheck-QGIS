import os
from osgeo import ogr
from qgis.core import QgsGeometry
import pandas as pd
import numpy as np
from typing import Union
from collections import OrderedDict

from projektcheck.base import Database, Table, Workspace

driver = ogr.GetDriverByName('GPKG')

DATATYPES = {
    int: ogr.OFTInteger64,
    bool: ogr.OFSTBoolean,
    float: ogr.OFTReal,
    str: ogr.OFTString
}

class GeopackageWorkspace(Workspace):
    def __init__(self, name, database):
        self.name = name
        self.path = self.fn(database, name)
        if not name:
            raise ValueError('workspace name can not be empty')
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'{self.path} does not exist')
        self._conn = ogr.Open(self.path, 0 if database.read_only else 1)

    @staticmethod
    def fn(database, name):
        fn = os.path.join(database.base_path, name).rstrip('\\')
        if not fn.endswith('.gpkg'):
            fn += '.gpkg'
        return fn

    @classmethod
    def get_or_create(cls, name, database):
        path = cls.fn(database, name)
        if not os.path.exists(path):
            cls.create(name, database)
        return GeopackageWorkspace(name, database)

    @classmethod
    def create(cls, name, database, overwrite=False):
        path = cls.fn(database, name)
        if overwrite and os.path.exists(path):
            os.remove(path)
        driver.CreateDataSource(path)
        return GeopackageWorkspace(name, database)

    @property
    def tables(self):
        tables = [l.GetName() for l in self._conn]
        return tables

    def get_table(self, name: str, fields: list=None):
        if name not in self.tables:
            raise FileNotFoundError(f'layer {name} not found')
        return GeopackageTable(name, self, fields=fields)

    def create_table(self, name: str, fields: dict, geometry_type: str=None,
                     overwrite: bool=False, defaults: dict={}):
        '''
        geometry_type: str, optional
            adds geometry to layer, wkb geometry type string
        '''
        if overwrite and name in self.tables:
            self._conn.DeleteLayer(name)
        kwargs = {}
        if geometry_type:
            wkb_types = self.wkb_types
            geometry_type = 'wkb' + geometry_type
            if geometry_type not in wkb_types:
                raise ValueError(
                    f'geometry type {geometry_type} is unknown. Available'
                    f'types are:\n {wkb_types}'
                )
            geometry_type = getattr(ogr, geometry_type)
            kwargs['geom_type'] = geometry_type
        layer = self._conn.CreateLayer(name, **kwargs)
        for fieldname, typ in fields.items():
            dt = DATATYPES[typ]
            field = ogr.FieldDefn(fieldname, dt)
            layer.CreateField(field)
        return self.get_table(name)

    @property
    def wkb_types(self):
        return [a for a in ogr.__dict__.keys() if a.startswith('wkb')]

    def __repr__(self):
        return f"GeopackageWorkspace {self.name} {self.path}"

    def close(self):
        self._conn = None


class GeopackageTable(Table):
    def __init__(self, name, workspace: GeopackageWorkspace,
                 fields: list=None):
        self.workspace = workspace
        self.name = name
        self._where = None
        self._fields = None
        self._layer = self.workspace._conn.GetLayerByName(self.name)
        if self._layer is None:
            raise ConnectionError(f'layer {self.name} not found')
        if fields is not None:
            f = np.array(fields)
            isin = np.isin(f, np.array(list(self.fields.keys())))
            if not np.all(isin):
                notin = ', '.join(f[isin != True])
                raise ValueError(
                    f'fields "{notin}" are not in table {self.name}')
            self._fields = fields

    def filter(self, **kwargs):
        '''
        supported: __in, __gt, __lt
        '''
        terms = []
        for k, v in kwargs.items():
            if '__' not in k:
                if k not in self.fields:
                    raise ValueError(f'{k} not in fields')
                terms.append(f'{k} = {v}')
            elif k.endswith('__in'):
                vstr = [str(i) for i in v]
                terms.append(f'"{k.strip("__in")}" in ({",".join(vstr)})')
            elif k.endswith('__gt'):
                terms.append(f'"{k.strip("__gt")}" > {v}')
            elif k.endswith('__lt'):
                terms.append(f'"{k.strip("__lt")}" < {v}')
        # set where clause, clears filter if no kwargs
        self.where = ' and '.join(terms)

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
        self._layer.SetAttributeFilter(value)

    @property
    def fields(self):
        if self._fields is not None:
            return self._fields
        definition = self._layer.GetLayerDefn()
        fields = {}
        for i in range(definition.GetFieldCount()):
            defn = definition.GetFieldDefn(i)
            fields[defn.GetName()] = defn.GetTypeName()
        return fields

    def add(self, row: Union[dict, list], geom=None):
        fields = self.fields.keys()
        if isinstance(row, list):
            row = dict(zip(fields, row))
        feature = ogr.Feature(self._layer.GetLayerDefn())
        for field, value in row.items():
            if field not in fields:
                raise ValueError(f'{field} is not in fields of '
                                 f'table {self.name}')
            feature.SetField(field, value)
        if geom and isinstance(geom, QgsGeometry):
            geom = ogr.CreateGeometryFromWkt(geom.asWkt())
        if geom:
            feature.SetGeometry(geom)
        self._layer.CreateFeature(feature)

    def delete(self, **kwargs):
        '''warning: resets cursor'''
        prev_where = self._where
        self.filter(**kwargs)
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

    def create_workspace(self, name, overwrite=False):
        return GeopackageWorkspace.create(name, self, overwrite=overwrite)

    def get_table(self, name: str, workspace: str = '', fields=None):
        if not workspace:
            raise Exception('Geopackage backend does not support '
                            'tables without workspaces')
        return self.get_workspace(workspace).get_table(name, fields=fields)

    def get_or_create_workspace(self, name):
        return GeopackageWorkspace.get_or_create(name, self)

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
