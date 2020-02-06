import os
from osgeo import ogr, osr
from qgis.core import QgsGeometry
import pandas as pd
from typing import Union
from collections import OrderedDict
import shutil
import numpy as np
import datetime

from projektcheck.base.database import (Database, Table, Workspace, Feature,
                                        Field, FeatureCollection)

driver = ogr.GetDriverByName('GPKG')

DATATYPES = {
    int: ogr.OFTInteger64,
    bool: ogr.OFTInteger,
    float: ogr.OFTReal,
    str: ogr.OFTString,
    datetime.date: ogr.OFTDateTime
}


class GeopackageWorkspace(Workspace):
    def __init__(self, name, database):
        super().__init__(name, database)
        self.path = self._fn(database, name)
        if not name:
            raise ValueError('workspace name can not be empty')
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'{self.path} does not exist')
        self._conn = None

    @property
    def conn(self):
        if not(self._conn):
            self._conn = ogr.Open(
                self.path, 0 if self.database.read_only else 1)
        return self._conn

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
        tables = [l.GetName() for l in self.conn]
        return tables

    def get_table(self, name: str, field_names: list=None):
        if name not in self.tables:
            raise FileNotFoundError(f'layer {name} not found')
        return GeopackageTable(name, self, field_names=field_names)

    def create_table(self, name: str, fields: dict, geometry_type: str=None,
                     overwrite: bool=False, defaults={}, epsg=None):
        '''
        geometry_type: str, optional
            adds geometry to layer, wkb geometry type string
        '''
        if overwrite and name in self.tables:
            self.conn.DeleteLayer(name)
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
        if epsg is not None:
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(epsg)
            kwargs['srs'] = srs
        layer = self.conn.CreateLayer(name, **kwargs)
        for fieldname, typ in fields.items():
            dt = DATATYPES[typ]
            field = ogr.FieldDefn(fieldname, dt)
            if fieldname in defaults:
                default = str(defaults[fieldname])
                # string default needs enclosing ""
                if typ == str and not default.startswith('"'):
                    default = f'"{default}"'
                field.SetDefault(default)
            layer.CreateField(field)
        return self.get_table(name)

    @property
    def wkb_types(self):
        return [a for a in ogr.__dict__.keys() if a.startswith('wkb')]

    def __repr__(self):
        return f"GeopackageWorkspace {self.name} {self.path}"

    def close(self):
        del(self._conn)
        self._conn = None


class GeopackageTable(Table):
    id_field = 'fid'
    geom_field = 'geom'

    def __init__(self, name, workspace: GeopackageWorkspace,
                 field_names: list=None, filters: dict={}):
        self.workspace = workspace
        self.name = name
        self._where = ''
        self._layer = self.workspace.conn.GetLayerByName(self.name)
        if self._layer is None:
            raise ConnectionError(f'layer {self.name} not found')
        # reset filters (ogr remembers it even on new connecion)
        self.reset()
        if field_names:
            self.field_names = list(field_names)
        else:
            defn = self._layer.GetLayerDefn()
            self.field_names = [defn.GetFieldDefn(i).GetName()
                                for i in range(defn.GetFieldCount())]
        self._filters = {}
        self.filter(**filters)

    def copy(self):
        return GeopackageTable(self.name, self.workspace,
                               field_names=self.field_names,
                               filters=self._filters)

    def _ogr_feat_to_row(self, feat):
        if self.field_names is not None:
            items = OrderedDict([(f, feat[f]) for f in self.field_names
                                 if hasattr(feat, f)])
        else:
            items = OrderedDict(self._cursor.items())
        items[self.id_field] = feat.GetFID()
        geom = feat.geometry()
        if geom:
            geom = QgsGeometry.fromWkt(geom.ExportToWkt())
        items[self.geom_field] = geom
        return items

    def __iter__(self):
        self._layer.ResetReading()
        return self

    def __next__(self):
        cursor = self._layer.GetNextFeature()
        self._cursor = cursor
        if not cursor:
            raise StopIteration
        return self._ogr_feat_to_row(cursor)

    def __getitem__(self, idx):
        # there is no indexing of ogr layers, so just iterate
        length = len(self)
        if idx == -1:
            if length == 0:
                raise IndexError(f'table is empty')
            idx = length - 1
        elif idx >= length:
            raise IndexError(f'index {idx} exceeds table length of {length}')
        for i, feat in enumerate(self._layer):
            if i == idx:
                self._layer.ResetReading()
                return self._ogr_feat_to_row(feat)

    def reset(self):
        self._filters = {}
        self.where = ''
        self.spatial_filter()

    def reset_cursor(self):
        self._layer.ResetReading()
        self._cursor = None

    def filter(self, **kwargs):
        '''
        filtering django style
        supported: __in, __gt, __lt, __ne
        '''
        # ToDo: filter ids (geom maybe not)
        #       more filters
        terms = []
        #field_names = [field.name for field in self.fields()]
        # ToDo: if there it is eventually possible to filter OR you can't just
        # append filters to old ones
        # (but seperate  previous and new filters with brackets)
        self._filters.update(kwargs)
        field_dict = dict([(f.name, f) for f in self.fields()])

        def check_quotation(value, field):
            if field.datatype == str and not value.startswith('"'):
                value = f'"{value}"'
            return value

        for k, v in self._filters.items():
            split = k.split('__')
            field_name = split[0]
            matching_field = field_dict.get(field_name)
            if field_name == 'id':
                field_name = self.id_field
            elif not matching_field:
                raise ValueError(f'{field_name} not in fields')
            else:
                if isinstance(v, list):
                    v = [check_quotation(i, matching_field) for i in v]
                else:
                    v = check_quotation(v, matching_field)

            if len(split) == 1:
                terms.append(f'{field_name} = {v}')
            elif split[1] == 'in':
                vstr = [str(i) for i in v]
                terms.append(f'"{field_name}" in ({",".join(vstr)})')
            elif split[1] == 'gt':
                terms.append(f'"{field_name}" > {v}')
            elif split[1] == 'lt':
                terms.append(f'"{field_name}" < {v}')
            elif split[1] == 'ne':
                terms.append(f'"{field_name}" <> {v}')
        where = ' and '.join(terms)
        #if self.where:
            #where = f'({self.where}) and ({where})'
        self.where = where

    def spatial_filter(self, wkt=None):
        if wkt is not None:
            wkt = ogr.CreateGeometryFromWkt(wkt)
        self._layer.SetSpatialFilter(wkt)

    @property
    def filters(self):
        return self._filters

    @property
    def where(self):
        return self._where

    @where.setter
    def where(self, value):
        self._cursor = None
        self._where = value
        self._layer = self.workspace.conn.GetLayerByName(self.name)
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
            default = defn.GetDefault()
            if default == 'None':
                default = None
            # GetDefault returns strings -> need to cast
            if datatype and default is not None:
                if datatype == bool:
                    default = False if default in ['False', 'false', '0'] \
                        else True
                else:
                    default = datatype(default)
            fields.append(Field(datatype, name=name, default=default))
        return fields

    def add(self, **kwargs):
        geom = kwargs.pop(self.geom_field, None)
        feature = ogr.Feature(self._layer.GetLayerDefn())
        for field, value in kwargs.items():
            if field not in self.field_names:
                continue
                #raise ValueError(f'{field} is not in fields of '
                                 #f'table {self.name}')
            ret = feature.SetField(field, value)
        if geom:
            if not isinstance(geom, ogr.Geometry):
                if not isinstance(geom, str):
                    geom = geom.asWkt()
                geom = ogr.CreateGeometryFromWkt(geom)
            feature.SetGeometry(geom)
        ret = self._layer.CreateFeature(feature)
        if ret != 0:
            raise Exception(f'Feature could not be created in table {self.name}. '
                            f'Ogr declined creation with error code {ret}')
        return self._ogr_feat_to_row(feature)

    def add_field(self, field):
        '''
        add field to table
        creates if not existing
        '''
        dt = DATATYPES[field.datatype]
        name = field.name
        if not name:
            raise ValueError('The field needs a name to be added to the table')
        # create field if not existing
        if name not in [f.name for f in self.fields()]:
            f = ogr.FieldDefn(name, dt)
            default = field.default
            # string default needs enclosing ""
            if field.datatype == str and not default.startswith('"'):
                default = f'"{default}"'
            f.SetDefault(str(default))
            self._layer.CreateField(f)
            # set all existing rows to default value
            feat = self._layer.GetNextFeature()
            while feat:
                feat.SetField(name, default)
                self._layer.SetFeature(feat)
                feat = self._layer.GetNextFeature()
        if getattr(self, '_fields', None):
            self._fields.append(field)
        self.field_names.append(name)

    def delete(self, id):
        self._layer.DeleteFeature(id)

    def set(self, id, **kwargs):
        feature = self._layer.GetFeature(id)
        if not feature:
            return False
        geom = kwargs.pop(self.geom_field, None)
        if geom:
            geom = ogr.CreateGeometryFromWkt(geom.asWkt())
        feature.SetGeometry(geom)
        for field_name, value in kwargs.items():
            feature.SetField(field_name, value)
        self._layer.SetFeature(feature)
        return True

    def get(self, id):
        feat = self._layer.GetFeature(id)
        return self._ogr_feat_to_row(feat)

    def delete_rows(self, **kwargs):
        '''warning: resets cursor'''
        prev_where = self.where
        self.filter(**kwargs)
        i = 0
        for feature in self._layer:
            self._layer.DeleteFeature(feature.GetFID())
            i += 1
        self.where = prev_where
        return i

    def update_cursor(self, row: Union[dict, list]):
        if isinstance(row, list):
            row = dict(zip(self.field_names, row))
        for field_name, value in row.items():
            if field_name == self.id_field:
                continue
            if field_name == self.geom_field:
                if value:
                    value = ogr.CreateGeometryFromWkt(value.asWkt())
                self._cursor.SetGeometry(value)
                continue
            self._cursor.SetField(field_name, value)
        self._layer.SetFeature(self._cursor)

    def to_pandas(self):
        rows = []
        for row in self:
            rows.append(row)
        df = pd.DataFrame.from_records(
            rows, columns=[self.id_field, self.geom_field] + self.field_names)
        return df

    def update_pandas(self, dataframe, pkeys=None):
        '''
        pkeys passed: looks for existing entry
        defaults to id if no pkeys given (id field is 'fid' by default)

        rows with no match will be added to table
        rows with matching pkeys (or id) will be updated (all fields overwritten
        with column values)

        '''
        def isnan(v):
            if isinstance(v, (np.integer, np.floating, float)):
                return np.isnan(v)
            return v is None

        for i, df_row in dataframe.iterrows():
            items = df_row.to_dict()
            geom = items.get('geom', None)
            if isnan(geom):
                items['geom'] = None
            # no pkeys: take id field directly
            pk = items.pop(self.id_field, None)
            # if pkeys are given, find id of matching feature
            if pkeys:
                pk = None
                filter_args = dict([(k, items[k]) for k in pkeys])
                l_nan = [isnan(p) for p in filter_args.values()]
                # no key should be nan or None
                if sum(l_nan) == 0:
                    prev_where = self.where
                    prev_filters = self._filters.copy()
                    self.filter(**filter_args)
                    if len(self) == 1:
                        pk = self[0][self.id_field]
                    if len(self) > 1:
                        self.where = prev_where
                        raise ValueError('more than one feature is matching '
                                         f'{filter_args}')
                    self.where = prev_where
                    self._filters = prev_filters

            if not isnan(pk):
                success = self.set(int(pk), **items)
                if not success:
                    self.add(**items)
            else:
                self.add(**items)

    def __len__(self):
        count = self._layer.GetFeatureCount()
        return 0 if count < 0 else count

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
