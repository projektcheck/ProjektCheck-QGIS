# -*- coding: utf-8 -*-
'''
***************************************************************************
    database.py
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

generic database interface and feature classes using this interface
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'

from abc import ABC
from typing import Union
import weakref


class Field:
    '''
    single field of a feature representing a column in the database

    Attributes
    ----------
    name : str
        the name of the field
    datatype : type
        basic data type of field
    default : object
        default value of the field
    '''
    def __init__(self, datatype, default=None, name=''):
        '''
        Parameters
        ----------
        name : str, optional
            the name of the field,
            should match the column name in the database if given
        datatype : type
            basic data type of field
        default : object, optional
            default value of the field (should match type)
        '''
        self.name = name
        self.datatype = datatype
        self.default = default

    def __repr__(self):
        return f'Field {self.name} {self.datatype}'


class Feature:
    '''
    Feature representing a row in a database table with it's column values
    as fields

    Attributes
    ----------
    id : int
        unique identifier of the feature
    table : Table
        database table the feature is linked to
    geom : QgsGeometry
        geometry of the feature
    '''
    def __init__(self, table, id=None, geom=None, **kwargs):
        '''
        Parameters
        ----------
        table : Table
            database table the feature is linked to
        id : int, optional
            unique identifier of the feature, leave empty if it is a new
            database entry
        geom : QgsGeometry, optional
            geometry of the feature
        **kwargs
            field values, field name as key and value of field as value
        '''
        self.__dict__['_fields'] = {f.name: f for f in table.fields()}
        self.id = id
        self.geom = geom
        self.table = table
        self._fields = []
        for f in table.fields():
            self._fields.append(f.name)
            v = kwargs.get(f.name, None)
            if v is None:
                v = f.default
            self.__dict__[f.name] = v

    def __getitem__(self, idx):
        if idx not in self._fields:
            raise KeyError(idx)
        return getattr(self, idx)

    def __setitem__(self, idx, value):
        if idx not in self._fields:
            raise KeyError(idx)
        setattr(self, idx, value)

    def save(self):
        '''
        store current state of features in database
        '''
        kwargs = {f: getattr(self, f) for f in self._fields}
        if self.geom and hasattr(self.geom, 'isGeosValid') \
           and not self.geom.isGeosValid():
            self.geom = self.geom.makeValid()
        kwargs[self.table.geom_field] = self.geom
        if self.id is not None:
            self.table.set(self.id, **kwargs)
        else:
            row = self.table.add(**kwargs)
            self.id = row[self.table.id_field]

    def delete(self):
        '''
        delete feature from database (identified by id)
        '''
        self.table.delete(self.id)

    def __repr__(self):
        return f'Feature <{self.id}> of {self.table}'


class FeatureCollection:
    '''
    iterable collection of features linked to the same database table,
    can be indexed with index 0..length

    Attributes
    ----------
    table : Table
        database table the features are linked to
    workspace : Workspace
        the workspace the features are in
    '''
    def __init__(self, table: 'Table'):
        '''
        Parameters
        ----------
        table : Table
            database table the features are in
        '''
        self.table = table
        self._it = 0

    def __iter__(self):
        self.table.reset_cursor()
        return self

    def __next__(self):
        if self._it >= len(self.table):
            self._it = 0
            self.table.reset_cursor()
            raise StopIteration
        else:
            row = next(self.table)
            self._it += 1
            return self._row_to_feature(row)

    def __len__(self):
        return len(self.table)

    def delete(self, **kwargs):
        '''
        delete features matching given filter keyword arguments;
        if no filter arguments are given, all features (in current filter
        state of collection) are deleted

        Parameters
        ----------
        **kwargs
            field filters, field name as key and value to match or
            field filter names as key (Django-style) and values to match;
            if multiple filters are passed every single one has to match
            (AND-linked);
            available filters depend on implementation of underlying database

            available filters for geopackages:
                <field-name>__in : list
                    values of field have to match any value in the list
                <field-name>__gt : object
                    values of field have to be greater than value
                <field-name>__lt : object
                    values of field have to be less than value
                <field-name>__ne : object
                    values of field has to be not equal to value

            e.g. employees.delete(name='Thomas Müller')
            employees.delete(name__in=['Thomas Müller', 'Hans Müller'])
            employees.delete(income__gt=60000, age__lt=65)
        '''
        if len(kwargs) > 0:
            prev_where = self.table.where
            ids = [feat.id for feat in self.filter(**kwargs)]
            # reset filter
            # ToDo: fix filter side effects
            self.table.where = prev_where
        else:
            # delete all features
            ids = [feat.id for feat in self]
        for id in ids:
            self.table.delete(id)

    def values(self, field_name: str) -> list:
        '''
        Parameters
        ----------
        field_name : str
            name of the field

        Returns
        -------
        list
            values of the given field in all features of this collection
        '''
        return self.table.values(field_name)

    @property
    def workspace(self) -> 'Workspace':
        '''
        workspace of underlying table
        '''
        return self.table.workspace

    def get(self, **kwargs):
        '''
        get a single feature; has to be unique for given filter keyword
        arguments

        Parameters
        ----------
        **kwargs
            field filters, field name as key and value to match or
            field filter names as key (Django-style) and values to match;
            @see filter(self, **kwargs) for more information filters

            e.g. employees.get(name='Thomas Müller')

        Returns
        -------
        Feature
            feature matching the filters or None if no match found

        Raises
        ------
        ValueError
            if more than feature match the given filter arguments
        '''
        table = self.table.copy()
        prev_where = table.where
        # filter table to match
        table.filter(**kwargs)
        if len(table) > 1:
            raise ValueError('get returned more than one feature')
        if len(table) == 0:
            row = None
        else:
            row = self._row_to_feature(table[0])
        # reset filter
        table.where = prev_where
        return row

    def add(self, **kwargs):
        '''
        add a new feature to the collection

        Parameters
        ----------
        **kwargs
            field values, field name as key and value of field as value
            e.g. employees.add(name='Thomas Müller')

        Raises
        ------
        ValueError
            if id is given
        '''
        if 'id' in kwargs:
            raise ValueError("You can't set the id when adding a new feature. "
                             "The id will be assigned automatically.")
        feature = Feature(self.table, **kwargs)
        feature.save()
        return feature

    def fields(self):
        '''
        available fields for each feature

        Returns
        -------
        list
            list of Field objects
        '''
        return self.table.fields()

    def add_field(self, field):
        '''
        add a field to the collection (applies to all features)

        Parameters
        ----------
        field : Field
            the field to add
        '''
        self.table.add_field(field)

    def reset(self):
        '''
        reset filters
        '''
        self.table.reset()

    def filter(self, **kwargs):
        '''
        filters this collection with given filters. If this collection was
        already filtered, the filters are applied on top (AND-linked)

        Parameters
        ----------
        **kwargs
            field filters, field name as key and value to match or
            field filter names as key (Django-style) and values to match;
            if multiple filters are passed every single one has to match
            (AND-linked);
            available filters depend on implementation of underlying database

            available filters for geopackages:
                <field-name>__in : list
                    values of field have to match any value in the list
                <field-name>__gt : object
                    values of field have to be greater than value
                <field-name>__lt : object
                    values of field have to be less than value
                <field-name>__ne : object
                    values of field has to be not equal to value

            e.g. employees.filter(name='Thomas Müller')
            employees.filter(name__in=['Thomas Müller', 'Hans Müller'])
            employees.filter(income__gt=60000, age__lt=65)

        Returns
        -------
        FeatureCollection
            filtered collection
        '''
        table = self.table.copy()
        table.filter(**kwargs)
        return FeatureCollection(table)

    def _row_to_feature(self, row):
        '''
        row in table to feature
        '''
        id = row.pop(self.table.id_field)
        geom = row.pop(self.table.geom_field)
        return Feature(table=self.table, id=id, geom=geom, **row)

    def __getitem__(self, idx):
        row = self.table[idx]
        return self._row_to_feature(row)

    def to_pandas(self, columns=[]):
        '''
        pandas representation of this (filtered) feature collection

        Returns
        -------
        Dataframe
            pandas dataframe containing the (filtered) features as rows and
            fields as columns
        '''
        return self.table.to_pandas(columns=columns)

    def update_pandas(self, dataframe, pkeys=None):
        '''
        updates database with data in given dataframe. columns of dataframe
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
        self.table.update_pandas(dataframe, pkeys=pkeys)


class Database(ABC):
    '''
    abstract class for managing connection to a database
    '''

    def __init__(self, read_only: bool = False):
        '''
        Parameters
        ----------
        read_only : bool
            flag for write access to the database and its workspaces
            (write access only if False)
        '''
        self.read_only = read_only
        self._workspaces = {}

    def create_workspace(self, name):
        '''
        create a workspace (physically)

        Parameters
        ----------
        name : str

            name of the workspace

        Returns
        -------
        Workspace
            the created workspace
        '''
        raise NotImplementedError

    def remove_workspace(self, name):
        '''
        remove a workspace (physically)

        Parameters
        ----------
        name : str
            name of the workspace
        '''
        raise NotImplementedError

    def get_table(self, name: str, workspace: str = '') -> 'Table':
        '''
        get table from database

        Parameters
        ----------
        name : str
            table name
        workspace : str, optional
            name of workspace (scheme or file), by default no workspace

        Returns
        -------
        Table
            the table
        '''
        raise NotImplementedError

    @property
    def workspaces(self):
        '''
        Returns
        -------
        list
            names of all available workspaces in this database
        '''
        raise NotImplementedError

    def get_workspace(self, name):
        '''
        get workspace by name

        Parameters
        ----------
        name : str
            name of the workspace

        Returns
        -------
        Workspace
            workspace with given name
        '''
        raise NotImplementedError

    def get_or_create_workspace(self, name):
        '''
        get workspace by name, if it not exists it will be created (physically)

        Parameters
        ----------
        name : str
            name of the workspace

        Returns
        -------
        Workspace
            the workspace with given name
        '''

    def close(self):
        '''
        close database connection
        '''
        raise NotImplementedError


class Workspace:
    '''
    abstract class for a workspace (e.g. file for file based databases or
    a scheme in a SQL database)

    Attributes
    ----------
    tables : list
        names of available tables in workspace
    '''
    __refs__ = [] # references to all open workspaces

    def __init__(self, name: str, database: Database):
        '''
        Parameters
        ----------
        name : str
            name of workspace
        database : Database
            the database the workspace is in
        '''
        self.name = name
        self.database = database
        # add reference to this workspace
        self.__refs__.append(weakref.ref(self))

    def get_table(self, name):
        '''
        get table from workspace

        Parameters
        ----------
        name : str
            table name

        Returns
        -------
        Table
        '''
        return self.database.get_table(name, self)

    @property
    def tables(self):
        raise NotImplementedError

    @classmethod
    def get_instances(cls):
        '''
        iterator over all instances of Workspaces
        '''
        for inst_ref in cls.__refs__:
            inst = inst_ref()
            if inst is not None:
                yield inst

    def close(self):
        '''
        close connection of workspace to source
        '''
        # remove this workspace from collected workspace references
        if weakref.ref(self) in self.__refs__:
            self.__refs__.remove(weakref.ref(self))
        del(self)


class Table(ABC):
    '''
    abstract class for an iterable database table

    Attributes
    ----------
    filters : dict
        active field filters
    where : str
        active filter string (depending on database)
    '''
    # override: has to match the name of the id column
    id_field = '__id__'
    # override: has to match the name of the geometry column
    geom_field = '__geom__'

    def __init__(self, name: str, workspace: Union[Workspace, str] = None,
                 field_names: list=None, where=''):
        self.name = name
        self.workspace = workspace
        self.where = where

    @property
    def where(self):
        '''
        currently active filter expression
        '''
        return self._where

    @where.setter
    def where(self, value):
        self._where = value

    def __iter__(self):
        return self

    def __next__(self):
        '''
        override for iterating rows

        Returns
        -------
        row : dict
            dictionary with field names as keys and values of fields as values
            representing the content of a single row
            if id is available it has to be added as key {self.id_field}
        '''
        raise NotImplementedError

    def fields(self, cached=True):
        '''
        all table fields with their types and defaults

        Returns
        -------
        list
            list of Field objects
        '''
        raise NotImplementedError

    def features(self):
        '''
        override to cache features

        Returns
        -------
        features : FeatureCollection
        '''
        return FeatureCollection(self)

    def to_pandas(self, columns=[]):
        '''
        override

        Returns
        -------
        dataframe : Dataframe
            pandas dataframe with field names as column names containing all
            rows in table
        '''
        raise NotImplementedError

    def __len__(self):
        '''
        override

        Returns
        -------
        count : int
            number of rows (features)
        '''
        raise NotImplementedError