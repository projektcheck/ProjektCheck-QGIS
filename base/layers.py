# -*- coding: utf-8 -*-
'''
***************************************************************************
    layers.py
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

layer wrappers to organize layers in the layer tree
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'

from abc import ABC
from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer,
                       QgsCoordinateTransform, QgsLayerTreeGroup,
                       QgsLayerTreeLayer)
from qgis.utils import iface
from typing import List


def nest_groups(parent: QgsLayerTreeGroup, groupnames: List[str],
                prepend: bool=True) -> QgsLayerTreeGroup:
    '''recursively nests groups in order of groupnames'''
    if len(groupnames) == 0:
        return parent
    next_parent = parent.findGroup(groupnames[0])
    if not next_parent:
        next_parent = (parent.insertGroup(0, groupnames[0])
                       if prepend else parent.addGroup(groupnames[0]))
    return nest_groups(next_parent, groupnames[1:], prepend=prepend)


class Layer(ABC):
    '''
    wrapper of a vector layer in the QGIS layer tree with some
    convenience functions. Can be grouped and addressed by its name.
    '''

    def __init__(self, layername: str, data_path: str, groupname: str = '',
                 prepend: bool = True):
        '''
        Parameters
        ----------
        layername : str
            name of the layer in the data source
        data_path : str
            path to the data source of the layer
        groupname : str, optional
            name of the parent group the layer will be added to, will be created
            if not existing, can be nested by joining groups with '/'
            e.g. 'Projekt/Hintergrundkarten',
            defaults to add layer to the root of the layer tree
        prepend : bool
            prepend the group of the layer if True (prepends each group if
            nested), append if False, defaults to prepending the group
        '''
        self.layername = layername
        self.data_path = data_path
        self.layer = None
        self._l = None
        self.groupname = groupname
        self.prepend = prepend
        self.canvas = iface.mapCanvas()

    @property
    def parent(self) -> QgsLayerTreeGroup:
        '''
        the parent group of the layer
        '''
        parent = QgsProject.instance().layerTreeRoot()
        if self.groupname:
            parent = Layer.add_group(self.groupname, prepend=self.prepend)
        return parent

    @property
    def tree_layer(self) -> QgsLayerTreeLayer:
        '''
        tree representation of the layer
        '''
        if not self.layer:
            return None
        return self.parent.findLayer(self.layer)

    @property
    def layer(self) -> QgsVectorLayer:
        '''
        the wrapped vector layer
        '''
        try:
            layer = self._layer
            if layer is not None:
                # call function on layer to check if it still exists
                layer.id()
        except RuntimeError:
            return None
        return layer

    @layer.setter
    def layer(self, layer):
        self._layer = layer

    @classmethod
    def add_group(cls, groupname: str, prepend: bool = True
                  ) -> QgsLayerTreeGroup:
        '''
        add a group to the layer tree

        Parameters
        ----------
        groupname : str
            name of the group that will be created, can be nested by joining
            groups with '/' e.g. 'Projekt/Hintergrundkarten'
        prepend : bool, optional
            prepend the group if True (prepends each group if nested),
            append if False, defaults to prepending the group

        Returns
        ----------
        QgsLayerTreeGroup
            the created group (the deepest one in hierarchy if nested)
        '''
        groupnames = groupname.split('/')
        parent = QgsProject.instance().layerTreeRoot()
        group = nest_groups(parent, groupnames, prepend=prepend)
        return group

    @classmethod
    def find(cls, label: str, groupname: str = '') -> List[QgsLayerTreeLayer]:
        '''
        deep find tree layer by name in a group recursively

        Parameters
        ----------
        label : str
            label of the tree layer
        groupname : str, optional
            name of the group to search in, can be nested by joining groups with
            '/' e.g. 'Projekt/Hintergrundkarten', defaults to searching in layer
            tree root

        Returns
        ----------
        list
            list of tree layers matching the name, empty list if none found
        '''
        parent = cls.find_group(groupname)
        if not parent:
            return []

        def deep_find(node, label):
            found = []
            if node:
                for child in node.children():
                    if child.name() == label:
                        found.append(child)
                    found.extend(deep_find(child, label))
            return found

        found = deep_find(parent, label)
        return found

    @classmethod
    def find_group(cls, groupname: str) -> QgsLayerTreeGroup:
        '''
        find a group in the layer tree by name

        Parameters
        ----------
        groupname : str
            name of the group to search, can be nested by joining groups with
            '/' e.g. 'Projekt/Hintergrundkarten'
        '''
        parent = QgsProject.instance().layerTreeRoot()
        groupnames = groupname.split('/')
        while groupnames:
            g = groupnames.pop(0)
            parent = parent.findGroup(g)
            if not parent:
                return
        return parent

    def draw(self, style_path: str = None, label: str = '', redraw: str = True,
             checked: bool = True, filter: str = None, expanded: bool = True,
             prepend: bool = False, uncheck_siblings: bool = False,
             toggle_if_exists=False) -> QgsVectorLayer:
        '''
        load the data into a vector layer, draw it and add it to the layer tree

        Parameters
        ----------
        label : str, optional
            label of the layer, defaults to layer name this is initialized with
        style_path : str, optional
            a QGIS style (.qml) can be applied to the layer, defaults to no
            style
        redraw : bool, optional
            replace old layer with same name in same group if True,
            only create if not existing if set to False, else it is refreshed,
            defaults to redrawing the layer
        checked: bool, optional
            set check state of layer in layer tree, defaults to being checked
        filter: str, optional
            QGIS filter expression to filter the layer, defaults to no filtering
        expanded: str, optional
            sets the legend to expanded or not, defaults to an expanded legend
        prepend: bool, optional
            prepend the layer to the other layers in its group if True,
            append it if False, defaults to appending the layer
        uncheck_siblings: bool, optional
            uncheck other layers in same group, defaults to leave their
            check-state as is
        toggle_if_exists: bool, optional
            toggle visibility if layer is already in layer tree, overrides
            "checked" parameter, ignored when redraw is True, defaults to set
            visibility according to given  "checked" parameter

        Returns
        ----------
        QgsVectorLayer
            the created, replaced or refreshed vector layer

        '''
        if not self.layer:
            layers = Layer.find(label, groupname=self.groupname)
            if layers:
                self.layer = layers[0].layer()
        if redraw:
            self.remove()

        if not self.layer:
            self.layer = QgsVectorLayer(self.data_path, self.layername, "ogr")
            if label:
                self.layer.setName(label)
            QgsProject.instance().addMapLayer(self.layer, False)
            self.layer.loadNamedStyle(style_path)
        else:
            self.canvas.refreshAllLayers()
        tree_layer = self.tree_layer
        if not tree_layer:
            tree_layer = self.parent.insertLayer(0, self.layer) if prepend else\
                self.parent.addLayer(self.layer)
        elif toggle_if_exists:
            checked = not tree_layer.isVisible()

        if uncheck_siblings:
            for child in self.parent.children():
                if child == tree_layer:
                    continue
                child.setItemVisibilityChecked(False)

        tree_layer.setItemVisibilityChecked(checked)
        tree_layer.setExpanded(expanded)
        if filter is not None:
            self.layer.setSubsetString(filter)
        return self.layer

    def set_visibility(self, state: bool):
        '''
        change check state of layer, layer is not visible if unchecked

        Parameters
        ----------
        state: bool
            set check state of layer in layer tree
        '''
        tree_layer = self.tree_layer
        if tree_layer:
            tree_layer.setItemVisibilityChecked(state)

    def zoom_to(self):
        '''
        zooms map canvas to the extent of this layer
        '''
        if not self.layer:
            return
        self.layer.updateExtents()
        extent = self.layer.extent()
        if not extent.isEmpty():
            transform = QgsCoordinateTransform(
                self.layer.crs(), self.canvas.mapSettings().destinationCrs(),
                QgsProject.instance())
            self.canvas.setExtent(transform.transform(extent))

    def remove(self):
        '''
        remove the layer from map and layer tree
        '''
        if not self.layer:
            return
        QgsProject.instance().removeMapLayer(self.layer.id())
        self.layer = None


class TileLayer(Layer):
    '''
    wrapper for a tile layer
    '''

    def __init__(self, url: str, groupname: str = '', prepend: bool = True):
        '''
        Parameters
        ----------
        url : str
            url of the tile layer service
        groupname : str, optional
            name of the parent group, will be created if not existing, can be
            nested by joining groups with '/' e.g. 'Projekt/Hintergrundkarten',
            defaults to adding layer to the root of the layer tree
        prepend : bool
            prepend the group of the layer if True (prepends each group if
            nested), append if False, defaults to prepending the group
        '''
        super().__init__(None, None, groupname=groupname, prepend=prepend)
        self.url = url
        self.prepend = prepend

    def draw(self, label: str, checked: bool = True, expanded: bool = True,
             toggle_if_exists=False):
        '''
        create the tile layer, draw it and add it to the layer tree

        Parameters
        ----------
        label : str
            label of the layer as it appears in the layer tree
        expanded : bool, optional
            replace old layer with same name in same group if True,
            only create if not existing if set to False, else it is refreshed,
            defaults to redrawing the layer
        checked: bool, optional
            set check state of layer in layer tree, defaults to being checked
        toggle_if_exists: bool, optional
            toggle visibility if layer is already in layer tree, overrides
            "checked" parameter, defaults to set visibility according to given
            "checked" parameter
        '''
        self.layer = None
        for child in self.parent.children():
            if child.name() == label:
                self.layer = child.layer()
                break
        if not self.layer:
            self.layer = QgsRasterLayer(self.url, label, 'wms')
            QgsProject.instance().addMapLayer(self.layer, False)
        tree_layer = self.tree_layer
        if not tree_layer:
            tree_layer = self.parent.insertLayer(0, self.layer) if self.prepend\
                else self.parent.addLayer(self.layer)
        elif toggle_if_exists:
            checked = not tree_layer.isVisible()
        tree_layer.setItemVisibilityChecked(checked)
        tree_layer.setExpanded(expanded)
