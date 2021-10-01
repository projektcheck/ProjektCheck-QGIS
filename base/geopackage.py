# -*- coding: utf-8 -*-
'''
***************************************************************************
    geopackage.py
    ---------------------
    Date                 : July 2019
    Copyright            : (C) 2019 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

geopackage database connection implementing the database interface
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'

import os
from osgeo import ogr, osr
from qgis.core import QgsGeometry
import pandas as pd
from typing import Union, List
from collections import OrderedDict
import numpy as np
import datetime

from .database import Database, Table, Workspace, Field

driver = ogr.GetDriverByName('GPKG')

# available datatypes (<python base type> : <ogr data type>)
DATATYPES = {
    int: ogr.OFTInteger64,
    bool: ogr.OFTInteger,
    float: ogr.OFTReal,
    str: ogr.OFTString,
    datetime.date: ogr.OFTDateTime
}


class GeopackageWorkspace(Workspace):
    '''
    manages the connection to a tables in a geopackage file

    Attributes
    ----------
    conn : DataSource
        ogr connection to geopackage file
    tables : list
        names of available tables in workspace
    wkb_types : list
        names of available ogr geometry types
    '''
    def __init__(self, name: str, database: Database):
        '''
        Parameters
        ----------
        name : str
            name of workspace, equals geopackage file name without
            ".gpkg" extension
        database : Geopackage
            the database the workspace is in, base path of database allocates
            path of geopackage file
        '''
        super().__init__(name, database)
        self.path = self._fn(database, name)
        if not name:
            raise ValueError('workspace name can not be empty')
        if not os.path.exists(self.path):
            raise FileNotFoundError(f'{self.path} does not exist')
        self._conn = None

    @property
    def conn(self) -> ogr.DataSource:
        ''' ogr connection '''
        if not(self._conn):
            self._conn = ogr.Open(
                self.path, 0 if self.database.read_only else 1)
        return self._conn

    @staticmethod
    def _fn(database: Database, name: str) -> str:
        '''
        path to geopackage file (incl. file name and ".gpkg" extension)
        '''
        fn = os.path.join(database.base_path, name).rstrip('\\')
        if not fn.endswith('.gpkg'):
            fn += '.gpkg'
        return fn

    @classmethod
    def get_or_create(cls, name: str, database: Database
                      ) -> 'GeopackageWorkspace':
        '''
        get workspace in database, create it if not existing (creates also the
        geopackage file with same name + "gpkg" extension)

        Parameters
        ----------
        name : str
            name of workspace

        Returns
        -------
        GeopackageWorkspace
        '''
        path = cls._fn(database, name)
        if not os.path.exists(path):
            if database.read_only:
                raise PermissionError('database is read-only')
            cls.create(name, database)
        return GeopackageWorkspace(name, database)

    @classmethod
    def create(cls, name: str, database: Database,
               overwrite: bool = False) -> 'GeopackageWorkspace':
        '''
        create workspace in database, creates the geopackage file name +
        "gpkg" extension in base path of database

        Parameters
        ----------
        name : str
            name of workspace
        database : Geopackage
            the database to put the workspace in

        Returns
        -------
        GeopackageWorkspace
        '''
        path = cls._fn(database, name)
        if overwrite and os.path.exists(path):
            os.remove(path)
        driver.CreateDataSource(path)
        return GeopackageWorkspace(name, database)

    @property
    def tables(self) -> List[str]:
        '''
        names of available tables
        '''
        tables = [l.GetName() for l in self.conn]
        return tables

    def get_table(self, name: str, field_names: list=None) -> 'GeopackageTable':
        '''
        get table from workspace

        Parameters
        ----------
        name : str
            name of table
        field_names : list, optional
            names of fields to show in table, others will be hidden,
            defaults to show all fields

        Returns
        -------
        GeopackageTable
        '''
        if name not in self.tables:
            raise FileNotFoundError(f'layer {name} not found')
        return GeopackageTable(name, self, field_names=field_names)

    def create_table(self, name: str, fields: dict, geometry_type: str = None,
                     overwrite: bool = False, defaults={},
                     epsg: int = None) -> 'GeopackageTable':
        '''
        creates table in workspace (geopackage)

        Parameters
        ----------
        name : str
            table name
        fields : dict
            dictionary of Fields in table with field names as keys and basic
            data types as values
        defaults : dict, optional
            default values for given fields with field names as keys and
            default values as values, defaults to no defaults
        geometry_type: str, optional
            adds geometry to layer, wkb geometry type string
        epsg : int, optional
            epsg code, sets srs of geometry field in geopackage table,
            defaults to no specific code
        overwrite : bool
            overwrites file if already exists if True, defaults to not
            overwriting

        Returns
        -------
        GeopackageTable
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
    def wkb_types(self) -> List[str]:
        ''' ogr geometry types '''
        return [a for a in ogr.__dict__.keys() if a.startswith('wkb')]

    def __repr__(self):
        return f"GeopackageWorkspace {self.name} {self.path}"

    def close(self):
        '''
        close ogr connection to geopackage file
        '''
        # self._conn.Destroy()
        del(self._conn)
        self._conn = None
        super().close()


class GeopackageTable(Table):
    '''
    iterable table connected to a geopackage table

    Attributes
    ----------
    filters : dict
        active field filters
    where : str
        active ogr filter string
    '''
    id_field = 'fid' # ogr default feature id field name
    geom_field = 'geom' # ogr default geometry field name

    def __init__(self, name: str, workspace: GeopackageWorkspace,
                 field_names: list = None, filters: dict = {}):
        '''
        Parameters
        ----------
        name : str
            name of table
        workspace : GeopackageWorkspace
            workspace (=geopackage file) the table is in
        field_names : list, optional
            names of fields to show in table, others will be hidden,
            defaults to show all fields
        filters : dict, optional
            field filters, field name as key and value to match or
            field filter names as key (Django-style) and values to match
        '''
        self.workspace = workspace
        self.name = name
        self._where = ''
        self._layer = self.workspace.conn.GetLayerByName(self.name)
        if self._layer is None:
            raise ConnectionError(f'layer {self.name} not found')
        # reset filters (ogr remembers them even on new connecion)
        self.reset()
        if field_names:
            self.field_names = list(field_names)
        else:
            defn = self._layer.GetLayerDefn()
            self.field_names = [defn.GetFieldDefn(i).GetName()
                                for i in range(defn.GetFieldCount())]
        self._filters = {}
        self.filter(**filters)

    def copy(self) -> 'GeopackageTable':
        '''
        copies this table, uses same ogr connection (via workspace)

        Returns
        -------
        GeopackageTable
        '''
        return GeopackageTable(self.name, self.workspace,
                               field_names=self.field_names,
                               filters=self._filters)

    def _ogr_feat_to_row(self, feat: ogr.Feature) -> dict:
        ''' ogr feature to table row (dict with field names as keys and field
        values as values) '''
        if self.field_names is not None:
            items = OrderedDict([(f, feat[f]) for f in self.field_names
                                 if hasattr(feat, f)])
        else:
            items = OrderedDict(self._cursor.items())
        items[self.id_field] = feat.GetFID()
        geom = feat.geometry()
        if geom:
            qgeom = QgsGeometry()
            qgeom.fromWkb(geom.ExportToWkb())
            if not qgeom.isGeosValid():
                qgeom = qgeom.makeValid()
            geom = qgeom
        items[self.geom_field] = geom
        return items

    def __iter__(self):
        self._layer.ResetReading()
        return self

    def __next__(self):
        cursor = self._layer.GetNextFeature()
        self._cursor = cursor
        if not cursor:
            self.reset_cursor()
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
        '''
        reset the filters (removes all filters)
        '''
        self._filters = {}
        self.where = ''
        self.spatial_filter()
        self.reset_cursor()

    def reset_cursor(self):
        '''
        reset the iterating cursor
        '''
        self._layer.ResetReading()
        self._cursor = None

    def filter(self, **kwargs):
        '''
        filter this table with given filters. If this table is
        already filtered, the filters are applied on top (AND-linked)

        Parameters
        ----------
        **kwargs
            field filters, field name as key and value to match or
            field filter names as key (Django-style) and values to match;
            if multiple filters are passed every single one has to match
            (AND-linked);

            available filters:
                <field-name>__in : list
                    values of field have to match any value in the list
                <field-name>__gt : object
                    values of field have to be greater than value
                <field-name>__lt : object
                    values of field have to be less than value
                <field-name>__ne : object
                    values of field has to be not equal to value

            e.g. table.filter(name='Thomas Müller')
            table.filter(name__in=['Thomas Müller', 'Hans Müller'])
            table.filter(income__gt=60000, age__lt=65)

        Returns
        -------
        GeopackageTable
            filtered table
        '''
        # ToDo: more filters
        terms = []
        #field_names = [field.name for field in self.fields()]
        # ToDo: if there it is eventually possible to filter OR you can't just
        # append filters to old ones
        # (but seperate  previous and new filters with brackets)
        self._filters.update(kwargs)
        field_dict = dict([(f.name, f) for f in self.fields()])

        def check_quotation(value, field):
            if field.datatype == str and (
                not isinstance(value, str) or not value.startswith('"')):
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

    def spatial_filter(self, wkt: str = None):
        '''
        sets spatial filter, features that do not geometrically intersect
        the filter geometry will be filtered out

        Parameters
        ----------
        wkt : str, optional
            geometry as well known text, the features intersecting the geometry
            remain, defaults to None (-> no spatial filtering)

        '''
        if wkt is not None:
            wkt = ogr.CreateGeometryFromWkt(wkt)
        self._layer.SetSpatialFilter(wkt)

    @property
    def filters(self) -> dict:
        '''
        active filters

        Returns
        -------
        dict
            filter expressions (django style)
        '''
        return self._filters

    @property
    def where(self) -> str:
        '''
        active ogr filter string

        Returns
        -------
        str
            filter string (ogr database style)
        '''
        return self._where

    @where.setter
    def where(self, value):
        self._cursor = None
        self._where = value
        self._layer = self.workspace.conn.GetLayerByName(self.name)
        self._layer.SetAttributeFilter(value)

    def fields(self, cached: bool = True) -> List[Field]:
        '''
        all table fields with their types and defaults

        Parameters
        ----------
        cached : bool, optional
            defaults to True
            True - cached fields if queried before (may not be up to date)
            False - up to date fields

        Returns
        -------
        list
            list of Field objects
        '''
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

    def add(self, **kwargs) -> dict:
        '''
        add a new row to the table, sets id if "fid" is passed

        Parameters
        ----------
        **kwargs
            field values, field name as key and value of field as value
            e.g. table.add(name='Thomas Müller')

        Returns
        -------
        dict
            added row with field names as keys, field values as values

        Raises
        ------
        Exception
            ogr error code while creating
        '''
        geom = kwargs.pop(self.geom_field, None)
        id = kwargs.pop(self.id_field, None)
        feature = ogr.Feature(self._layer.GetLayerDefn())
        if id is not None:
            feature.SetFID(id)
        for field, value in kwargs.items():
            if field not in self.field_names:
                continue
            if isinstance(value, np.integer):
                value = int(value)
            if isinstance(value, np.float):
                value = float(value)
            ret = feature.SetField(field, value)
        if geom:
            if not isinstance(geom, ogr.Geometry):
                # geometries as bytes are preferable
                if hasattr(geom, 'asWkb'):
                    geom = geom.asWkb().data()
                # some qgis geometries only support export to wkt
                elif hasattr(geom, 'asWkt'):
                    geom = geom.asWkt()
                if isinstance(geom, str):
                    geom = ogr.CreateGeometryFromWkt(geom)
                elif isinstance(geom, bytes):
                    geom = ogr.CreateGeometryFromWkb(geom)
                else:
                    raise Exception('unsupported geometry type')
            feature.SetGeometry(geom)
        ret = self._layer.CreateFeature(feature)
        if ret != 0:
            raise Exception(f'Feature could not be created in table {self.name}. '
                            f'Ogr declined creation with error code {ret}')
        return self._ogr_feat_to_row(feature)

    def add_field(self, field: Field):
        '''
        add a field to the table, will be created if not existing

        Parameters
        ----------
        field : Field
            the field to add
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
        if name not in self.field_names:
            self.field_names.append(name)

    def delete(self, id: int):
        '''
        delete row with given id

        Parameters
        ----------
        id : int
            id (as given by ogr) of feature to delete
        '''
        self._layer.DeleteFeature(id)

    def truncate(self):
        '''
        truncate the table removing all features in it
        '''
        self.workspace.conn.ExecuteSQL(
            f'DELETE FROM {self.name};', dialect='SQLITE')

    def values(self, field: Field) -> List[object]:
        '''
        Parameters
        ----------
        field : Field
            the field to return values of

        Returns
        -------
        list
            values of the given field in all features of this collection
        '''
        values = [f[field] for f in self._layer]
        return values

    def set(self, id: int, **kwargs) -> bool:
        '''
        sets given values to fields of row with given id

        Returns
        -------
        bool
            True - successful set
            False - row with id not found
        '''
        feature = self._layer.GetFeature(id)
        if not feature:
            return False
        if 'geom' in kwargs:
            geom = kwargs.pop(self.geom_field, None)
            if geom:
                geom = ogr.CreateGeometryFromWkt(geom.asWkt())
            feature.SetGeometry(geom)
        for field_name, value in kwargs.items():
            if isinstance(value, np.integer):
                value = int(value)
            if isinstance(value, np.float):
                value = float(value)
            feature.SetField(field_name, value)
        self._layer.SetFeature(feature)
        return True

    def get(self, id: int) -> dict:
        '''
        get row by id

        Returns
        -------
        dict
            field names as keys, field values as values
        '''

        feat = self._layer.GetFeature(id)
        return self._ogr_feat_to_row(feat)

    def delete_rows(self, **kwargs) -> int:
        '''
        deletes rows matching given filters (in addition to already existing
        filters)

        Parameters
        ----------
        **kwargs
             field filters, field name as key and value to match or
            field filter names as key (Django-style) and values to match

        Returns
        -------
        int
            number of deleted rows
        '''
        prev_where = self.where
        self.filter(**kwargs)
        i = 0
        for feature in self._layer:
            self._layer.DeleteFeature(feature.GetFID())
            i += 1
        self.where = prev_where
        return i

    def update_cursor(self, row: Union[dict, list]):
        '''
        update field values of current cursor position (while iterating)

        Parameters
        ----------
        row : dict or list
            dict - field names as keys and new values as values
        '''
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

    def to_pandas(self, columns: List[str] = []) -> pd.DataFrame:
        '''
        pandas representation of this (filtered) table

        Parameters
        ----------
        columns : list
            names of columns (fields) the returned dataframe should contain,
            defaults to all fields of table being represented as columns

        Returns
        -------
        Dataframe
            pandas dataframe containing the (filtered) table rows and
            fields as columns
        '''
        rows = []
        for row in self:
            rows.append(row)
        columns = columns or [self.id_field, self.geom_field] + self.field_names
        df = pd.DataFrame.from_records(rows, columns=columns)
        return df

    def update_pandas(self, dataframe: pd.DataFrame, pkeys: List[str] = None):
        '''
        updates table with data in given dataframe. columns of dataframe
        should match the field names, otherwise they will be ignored.
        Rows matching existing rows in the database (identified by the passed
        pkeys or the column named like the database id field by default)
        will be updated

        Parameters
        ----------
        dataframe : Dataframe
            pandas dataframe to add to the database
        pkeys : list, optional
            list of strings with column names used as primary keys
        '''
        def isnan(v):
            if isinstance(v, (np.integer, np.floating, float)):
                return np.isnan(v)
            return v is None

        for i, df_row in dataframe.iterrows():
            items = df_row.to_dict()
            if 'geom' in items and isnan(items['geom']):
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
                    items[self.id_field] = pk
                    self.add(**items)
            else:
                self.add(**items)

    def __len__(self) -> int:
        count = self._layer.GetFeatureCount()
        return 0 if count < 0 else count

    def __repr__(self):
        return f'GeopackageTable {self.name} {self._layer}'


class Geopackage(Database):
    '''
    manages the connection to geopackage files in a specific folder (base path)

    Attributes
    ----------
    read_only : bool
        flag for write access to the database and its workspaces
        (write access only if False)
    base_path : str
        path to geopackage file(s)
    workspaces : list
        names of available workspaces (=geopackages) in base path
    '''
    def __init__(self, base_path: str = '.', read_only: bool = False):
        '''
        Parameters
        ----------
        read_only : bool
            flag for write access to the database and its workspaces
            (write access only if False)
        base_path : str
            path to geopackage file(s)
        '''
        self.base_path = base_path
        self.read_only = read_only
        self._workspaces = {}

    def create_workspace(self, name: str, overwrite: bool = False
                         ) -> GeopackageWorkspace:
        '''
        create a workspace, creates a file with the given name
        (file extension ".gpkg" will be added) in the configured base path

        Parameters
        ----------
        name : str
            name of the workspace (file name without ".gpkg" extension)
        overwrite : bool
            True - overwrites file if already exists

        Returns
        -------
        GeopackageWorkspace
            the new workspace linking to the created file

        Raises
        ------
        PermissionError
            if database is flagged as read only
        '''
        if self.read_only:
            raise PermissionError('database is read-only')
        workspace = GeopackageWorkspace.create(name, self, overwrite=overwrite)
        self._workspaces[name] = workspace
        return workspace

    def remove_workspace(self, name: str):
        '''
        remove the workspace and the file it links to

        Parameters
        ----------
        name : str
            name of the workspace (file name without ".gpkg" extension)

        Raises
        ------
        PermissionError
            if database is flagged as read only
        '''
        if self.read_only:
            raise PermissionError('database is read-only')
        if not name.endswith('.gpkg'):
            name += '.gpkg'
        if name in self._workspaces:
            self._workspaces[name].close()
        os.remove(os.path.join(self.base_path, name))

    def get_table(self, name: str, workspace: str = '',
                  fields: List[str] = None) -> GeopackageTable:
        '''
        get table from database

        Parameters
        ----------
        name : str
            table name
        workspace : str, optional
            name of workspace (file name without extension),
            by default no workspace
        fields : str, optional
            names of the fields the table should contain, defaults to all fields
            that are present in the source

        Returns
        -------
        GeopackageTable
            the table
        '''
        if not workspace:
            raise Exception('Geopackage backend does not support '
                            'tables without workspaces')
        return self.get_workspace(workspace).get_table(name, field_names=fields)

    def get_or_create_workspace(self, name: str) -> GeopackageWorkspace:
        '''
        get workspace by name, if it not exists it will be created (including
        file with same name with ".gpkg" extension in the base path)

        Parameters
        ----------
        name : str
            name of the workspace

        Returns
        -------
        GeopackageWorkspace
            the workspace with given name

        Raises
        ------
        PermissionError
            if database is flagged as read only and workspace is not existing
            yet
        '''
        if name in self._workspaces:
            return self._workspaces[name]
        workspace = GeopackageWorkspace.get_or_create(name, self)
        self._workspaces[name] = workspace
        return workspace

    def get_workspace(self, name: str) -> GeopackageWorkspace:
        '''
        get workspace by name, workspace links to geopackage file with same
        name (".gpkg" file extension)

        Parameters
        ----------
        name : str
            name of the workspace (file name without extension)

        Returns
        -------
        GeopackageWorkspace
            workspace with given name
        '''
        if name in self._workspaces:
            workspace = self._workspaces[name]
        else:
            workspace = GeopackageWorkspace(name, self)
            self._workspaces[name] = workspace
        return workspace

    @property
    def workspaces(self) -> List[str]:
        ''' names of available workspaces'''
        workspaces = [f.rstrip('.gpkg') for f in os.listdir(self.base_path)
                      if os.path.isfile(os.path.join(self.base_path, f)) and
                      f.endswith('.gpkg')]
        return workspaces

    def __repr__(self):
        return f"Geopackage {self.base_path}"

    def close(self):
        '''
        closes all open workspaces
        '''
        for workspace in self._workspaces.values():
            workspace.close()
