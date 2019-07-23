import os
from osgeo import ogr
from qgis.core import QgsGeometry
import pandas as pd
import numpy as np
from typing import Union
from collections import OrderedDict
import shutil

from projektcheck.base import (Database, Table, Workspace, Feature, Field,
                               FeatureCollection)

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
        self.path = self._fn(database, name)
        if not name:
            raise ValueError('workspace name can not be empty')
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'{self.path} does not exist')
        self._conn = ogr.Open(self.path, 0 if database.read_only else 1)

    @staticmethod
    def _fn(database, name):
        fn = os.path.join(database.base_path, name).rstrip('\\')
        if not fn.endswith('.gpkg'):
            fn += '.gpkg'
        return fn

    @classmethod
    def get_or_create(cls, name, database):
        path = cls._fn(database, name)
        if not os.path.exists(path):
            if database.read_only:
                raise PermissionError('database is read-only')
            cls.create(name, database)
        return GeopackageWorkspace(name, database)

    @classmethod
    def create(cls, name, database, overwrite=False):
        path = cls._fn(database, name)
        if overwrite and os.path.exists(path):
            os.remove(path)
        driver.CreateDataSource(path)
        return GeopackageWorkspace(name, database)

    @property
    def tables(self):
        tables = [l.GetName() for l in self._conn]
        return tables

    def get_table(self, name: str, field_names: list=None, defaults: dict={}):
        if name not in self.tables:
            raise FileNotFoundError(f'layer {name} not found')
        return GeopackageTable(name, self, field_names=field_names,
                               defaults=defaults)

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
        return self.get_table(name, defaults=defaults)

    @property
    def wkb_types(self):
        return [a for a in ogr.__dict__.keys() if a.startswith('wkb')]

    def __repr__(self):
        return f"GeopackageWorkspace {self.name} {self.path}"

    def close(self):
        self._conn = None


class GeopackageTable(Table):
    def __init__(self, name, workspace: GeopackageWorkspace,
                 field_names: list=None, where: str='', defaults: dict={}):
        self.workspace = workspace
        self.name = name
        self._layer = self.workspace._conn.GetLayerByName(self.name)
        if self._layer is None:
            raise ConnectionError(f'layer {self.name} not found')
        self.where = where
        if field_names:
            self.field_names = field_names
        else:
            defn = self._layer.GetLayerDefn()
            self.field_names = [defn.GetFieldDefn(i).GetName()
                                for i in range(defn.GetFieldCount())]
        self._defaults = defaults

    def __next__(self):
        cursor = self._layer.GetNextFeature()
        self._cursor = cursor
        if not cursor:
            raise StopIteration
        if self.field_names is not None:
            items = OrderedDict([(f, cursor[f]) for f in self.field_names])
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

    def fields(self, cached=True):
        if cached and getattr(self, '_fields', None):
            return self._fields
        definition = self._layer.GetLayerDefn()
        fields = []
        rev_types = {v: k for k, v in DATATYPES.items()}
        for i in range(definition.GetFieldCount()):
            defn = definition.GetFieldDefn(i)
            name = defn.GetName()
            t = defn.GetType()
            datatype = rev_types[t] if t in rev_types else None
            default = self._defaults[name] if name in self._defaults else None
            fields.append(Field(datatype, name=name, default=default))
        return fields

    def add(self, row: Union[dict, list], geom=None):
        if isinstance(row, list):
            fields = [field.name for field in self.fields]
            row = dict(zip(fields, row))
        feature = ogr.Feature(self._layer.GetLayerDefn())
        for field, value in row.items():
            if field not in self.field_names:
                raise ValueError(f'{field} is not in fields of '
                                 f'table {self.name}')
            feature.SetField(field, value)
        if geom and isinstance(geom, QgsGeometry):
            geom = ogr.CreateGeometryFromWkt(geom.asWkt())
        if geom:
            feature.SetGeometry(geom)
        self._layer.CreateFeature(feature)

    def delete_feature(self, id):
        self._layer.DeleteFeature(id)

    def add_feature(self, feature):
        feat = ogr.Feature(self._layer.GetLayerDefn())
        for field in self.fields():
            feat.SetField(field.name, getattr(feature, field.name))
        geom = feature.geom
        if geom and isinstance(geom, QgsGeometry):
            geom = ogr.CreateGeometryFromWkt(geom.asWkt())
        if geom:
            feat.SetGeometry(geom)
        self._layer.CreateFeature(feat)
        feature.id = feat.GetFID()

    def set_feature(self, id, feature):
        feat = self._layer.GetFeature(id)
        for field in self.fields():
            feat.SetField(field.name, field.value)

    def get_feature(self, id):
        feat = self._layer.GetFeature(id)
        feature = Feature(self, self.fields())
        return feature

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
            row = dict(zip(self.field_names, row))
        for field, value in row.items():
            self._cursor.SetField(field, value)
            self._layer.SetFeature(self._cursor)

    def as_pandas(self):
        rows = []
        for row in self:
            rows.append(row.values())
        df = pd.DataFrame.from_records(rows, columns=self.field_names)
        return df

    def __len__(self):
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
        self._workspaces = {}

    def create_workspace(self, name, overwrite=False):
        if self.read_only:
            raise ('database is read-only')
        workspace = GeopackageWorkspace.create(name, self, overwrite=overwrite)
        self._workspaces[name] = workspace
        return workspace

    def remove_workspace(self, name):
        if self.read_only:
            raise PermissionError('database is read-only')
        if not name.endswith('.gpkg'):
            name += '.gpkg'
        if name in self._workspaces:
            self._workspaces[name].close()
        os.remove(os.path.join(self.base_path, name))

    def get_table(self, name: str, workspace: str = '', fields=None):
        if not workspace:
            raise Exception('Geopackage backend does not support '
                            'tables without workspaces')
        return self.get_workspace(workspace).get_table(name, field_names=fields)

    def get_or_create_workspace(self, name):
        if name in self._workspaces:
            return self._workspaces[name]
        workspace = GeopackageWorkspace.get_or_create(name, self)
        self._workspaces[name] = workspace
        return workspace

    def get_workspace(self, name):
        if name in self._workspaces:
            workspace = self._workspaces[name]
        else:
            workspace = GeopackageWorkspace(name, self)
            self._workspaces[name] = workspace
        return workspace

    @property
    def workspaces(self):
        workspaces = [f.rstrip('.gpkg') for f in os.listdir(self.base_path)
                      if os.path.isfile(os.path.join(self.base_path, f)) and
                      f.endswith('.gpkg')]
        return workspaces

    def __repr__(self):
        return f"Geopackage {self.base_path}"

    def close(self):
        for workspace in self._workspaces:
            workspace.close()
