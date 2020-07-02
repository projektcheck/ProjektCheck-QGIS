# -*- coding: utf-8 -*-
'''
***************************************************************************
    tools.py
    ---------------------
    Date                 : April 2019
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

tools to interact with the QGIS map canvas
'''

__author__ = 'Christoph Franke'
__date__ = '17/04/2019'

try:
    from shapely import geometry, wkt
    from shapely.ops import nearest_points
    SHAPELY_LOADED = True
# doesn't seem to load properly under MacOS
except:
    SHAPELY_LOADED = False

from typing import Union, List
from qgis.core import QgsGeometryUtils
from qgis import utils
from qgis.PyQt.QtCore import pyqtSignal, Qt, QTimer
from qgis.PyQt.QtGui import QCursor, QColor
from qgis.PyQt.QtWidgets import QWidget
from qgis.gui import (QgsMapToolEmitPoint, QgsMapToolIdentify, QgsRubberBand,
                      QgsVertexMarker)
from qgis.PyQt.QtWidgets import QToolTip
from qgis.core import (QgsFeature, QgsCoordinateTransform, QgsCurvePolygon,
                       QgsProject, QgsCoordinateReferenceSystem, QgsGeometry,
                       QgsPointXY, QgsPoint, QgsWkbTypes, QgsRectangle,
                       QgsVectorLayer)
from qgis.gui import QgsMapCanvas


class MapTool:
    '''
    abstract class for tools triggered by clicking a certain ui element

    Attributes
    ----------
    cursor : QCursor
        the appearance of the cursor when hovering the map canvas while tool is
        active
    '''
    cursor = QCursor(Qt.CrossCursor)

    def __init__(self, ui_element: QWidget, canvas: QgsMapCanvas = None,
                 tip: str = '', target_epsg: int = 25832):
        '''
        Parameters
        ----------
        ui_element : QWidget
            clickable UI element, clicking it will activate/deactivate this
            tool
        canvas : QgsMapCanvas, optional
            the map canvas the tool will work on, defaults to the map canvas of
            the QGIS UI
        tip : str, optional
            tooltip text shown while hovering the map canvas, defaults to not
            showing a tooltip
        target_epsg : int, optional
            all geometries determined by map interactions will be transformed
            into the crs with given epsg code, defaults to 25832
        '''
        self.ui_element = ui_element
        self.canvas = canvas or utils.iface.mapCanvas()
        # workaround: .clicked.connect(self.toggle) works only occasionally
        # reason unknown
        self.ui_element.clicked.connect(
            lambda checked: self.set_active(checked))
        self.tip = tip
        if tip:
            self.map_timer = QTimer(self.canvas)
            self.map_timer.timeout.connect(self.show_tip)
        self.target_crs = QgsCoordinateReferenceSystem(target_epsg)

    def transform_from_map(
        self, geom: Union[QgsGeometry, QgsPointXY, QgsRectangle]
        ) -> Union[QgsGeometry, QgsPointXY, QgsRectangle]:
        '''
        transform a geometry from the map canvas CRS to the target CRS
        (as provided by target_epsg on init)

        Parameters
        ----------
        geom : QgsGeometry or QgsPointXY or QgsRectangle
            geometry to transform (should be in target_epsg)

        Returns
        ----------
        QgsGeometry or QgsPointXY or QgsRectangle
            transformed geometry in target projection, type is same as
            input geometry
        '''
        source_crs = self.canvas.mapSettings().destinationCrs()
        tr = QgsCoordinateTransform(
            source_crs, self.target_crs, QgsProject.instance())
        if isinstance(geom, QgsGeometry):
            geom.transform(tr)
            return geom
        return tr.transform(geom)

    def transform_to_map(
        self, geom: Union[QgsGeometry, QgsPointXY, QgsRectangle]
        ) -> Union[QgsGeometry, QgsPointXY, QgsRectangle]:
        '''
        transform a geometry from the target CRS (as provided by target_epsg on
        init) into the map canvas projection to the target CRS

        Parameters
        ----------
        geom : QgsGeometry or QgsPointXY or QgsRectangle
            geometry to transform (should be in projection of map canvas)

        Returns
        ----------
        QgsGeometry or QgsPointXY or QgsRectangle
            transformed geometry in map canvas projection, type is same as
            input geometry
        '''
        target_crs = self.canvas.mapSettings().destinationCrs()
        xform = QgsCoordinateTransform(
            self.target_crs, target_crs, QgsProject.instance())
        if isinstance(geom, QgsGeometry):
            geom.transform(xform)
            return geom
        return xform.transform(geom)

    def set_active(self, active: bool):
        '''
        activate/deactivate the tool

        Parameters
        ----------
        active : bool
            activate tool if True, deactivate the tool if False
        '''
        if active:
            self.canvas.setMapTool(self)
            self.canvas.mapToolSet.connect(self.disconnect)
            self.canvas.setCursor(self.cursor)
        else:
            self.canvas.unsetMapTool(self)
            try:
                self.ui_element.blockSignals(True)
                self.ui_element.setChecked(False)
                self.ui_element.blockSignals(False)
            # ui element might already have been deleted by QGIS on changing
            # projects
            except RuntimeError:
                pass

    def disconnect(self, **kwargs):
        '''
        disconnect the tool from the map canvas
        '''
        self.canvas.mapToolSet.disconnect(self.disconnect)
        self.set_active(False)

    def canvasMoveEvent(self, e):
        '''
        override, hide tooltip on moving the mouse
        '''
        if self.tip and self.canvas.underMouse():
            QToolTip.hideText()
            self.map_timer.start(700)

    def show_tip(self):
        '''
        show the tooltip on the map
        '''
        if self.canvas.underMouse():
            QToolTip.showText(
                self.canvas.mapToGlobal(self.canvas.mouseLastXY()),
                self.tip, self.canvas)


class MapClickedTool(MapTool, QgsMapToolEmitPoint):
    '''
    tool for determing the positions of left mouse clicks on the canvas

    Attributes
    ----------
    map_clicked : pyqtSignal
        emitted when the map canvas is left clicked, emits point geometry with
        x,y-coordinates in target projection
    '''
    map_clicked = pyqtSignal(QgsGeometry)

    def __init__(self, ui_element: QWidget, tip: str = '',
                 canvas: QgsMapCanvas = None, target_epsg: int = 25832):
        '''
        Parameters
        ----------
        ui_element : QWidget
            clickable UI element, clicking it will activate/deactivate this
            tool
        canvas : QgsMapCanvas, optional
            the map canvas the tool will work on, defaults to the map canvas of
            the QGIS UI
        tip : str, optional
            tooltip text shown while hovering the map canvas, defaults to not
            showing a tooltip
        target_epsg : int, optional
            position of clicked coordinates on map canvas will be transformed
            into the crs with given epsg code, defaults to 25832
        '''
        MapTool.__init__(self, ui_element, target_epsg=target_epsg,
                         canvas=canvas, tip=tip)
        QgsMapToolEmitPoint.__init__(self, canvas=self.canvas)
        self.canvasClicked.connect(self._map_clicked)

    def _map_clicked(self, point: QgsPointXY, e):
        '''
        emit the signal with geometry
        '''
        geom = QgsGeometry.fromPointXY(point)
        self.map_clicked.emit(self.transform_from_map(geom))


class FeaturePicker(MapTool, QgsMapToolEmitPoint):
    '''
    tool for picking features on the map canvas by clicking

    Attributes
    ----------
    feature_picked : pyqtSignal
        emitted when a feature is clicked on the map canvas, emits the clicked
        feature
    '''
    feature_picked = pyqtSignal(QgsFeature)

    def __init__(self, ui_element: QWidget, layers: List[QgsVectorLayer] = [],
                 canvas: QgsMapCanvas = None):
        '''
        Parameters
        ----------
        ui_element : QWidget
            clickable UI element, clicking on it will adctivate/deactivate this
            tool
        layers : list, optional
            the layers containing the features that can be picked,
            defaults to not setting any layers
        canvas : QgsMapCanvas, optional
            the map canvas the tool will work on, defaults to the map canvas of
            the QGIS UI
        '''
        MapTool.__init__(self, ui_element, canvas=canvas)
        QgsMapToolEmitPoint.__init__(self, canvas=self.canvas)
        self._layers = layers

    def add_layer(self, layer: QgsVectorLayer):
        '''
        add a layer to pick features from

        Parameters
        ----------
        layer : QgsVectorLayer
            the layer containing the features that can be picked
        '''
        if layer:
            self._layers.append(layer)

    def set_layer(self, layer: QgsVectorLayer):
        '''
        sets a single layer to pick features from

        Parameters
        ----------
        layer : QgsVectorLayer
            the layer containing the features that can be picked
        '''
        if not layer:
            self._layers = []
        else:
            self._layers = [layer]

    def canvasReleaseEvent(self, mouseEvent):
        '''
        override, emit first feature found on mouse release
        '''
        if not self._layers:
            return
        features = QgsMapToolIdentify(self.canvas).identify(
            mouseEvent.x(), mouseEvent.y(), self._layers,
            QgsMapToolIdentify.TopDownStopAtFirst)
        if len(features) > 0:
            self.feature_picked.emit(features[0].mFeature)


class LineMapTool(MapTool, QgsMapToolEmitPoint):
    '''
    draw a line on the map (connected, multiple sections)

    Attributes
    ----------
    drawn : pyqtSignal
        emitted after double click or right click on the map canvas, emits the
        drawn line
    '''
    drawn = pyqtSignal(QgsGeometry)
    wkbtype = QgsWkbTypes.LineGeometry

    def __init__(self, ui_element: QWidget, canvas: QgsMapCanvas = None,
                 color: Union[str, int] = None, draw_markers=False,
                 line_width: int = 2, line_style: int = Qt.SolidLine,
                 snap_geometry: QgsGeometry = None, target_epsg: int = 25832):
        '''
        Parameters
        ----------
        ui_element : QWidget
            clickable UI element, clicking it will activate/deactivate this
            tool
        canvas : QgsMapCanvas, optional
            the map canvas the tool will work on, defaults to the map canvas of
            the QGIS UI
        color : int or str, optional
            color description, sets color of line and markers while
            drawing, defaults to blue
        draw_markers : bool, optional
            draw markers between segments of the line, defaults to no markers
        line_width : int, optional
            width of drawn lines in pixels, defaults to 2 pixels
        line_style : int, optional
            style of drawn lines (e.g. Qt.DashDotLine), defaults to solid line
        snap_geometry : QgsGeometry, optional
            snap drawn lines to outline of given geometry, defaults to no
            snapping
        target_epsg : int, optional
            projection of emitted geometry after drawing as epsg code,
            defaults to 25832
        '''
        self.canvas = canvas
        MapTool.__init__(self, ui_element, self.canvas)
        QgsMapToolEmitPoint.__init__(self, canvas=self.canvas)
        self.rubberband = QgsRubberBand(self.canvas,
                                           self.wkbtype)
        self.color = QColor(color) if color else QColor(0, 0, 255)
        self.rubberband.setColor(self.color)
        self.color.setAlpha(100)
        self.rubberband.setFillColor(self.color)
        self.rubberband.setLineStyle(line_style)
        self.rubberband.setWidth(line_width)

        self.snap_geometry = self.set_snap_geometry(snap_geometry)
        self.draw_markers = draw_markers
        if self.draw_markers:
            # auto points on outline should but doesn't work:
            #self.drawing_lines.setIcon(QgsRubberBand.ICON_CIRCLE)
            #self.drawing_lines.setIconSize(8)

            # drawing markers manually instead
            self.markers = []

        self._drawing = False
        self._moving =  False

        # marker for showing snapped point on move
        self._move_marker = QgsVertexMarker(self.canvas)
        self._move_marker.setColor(self.color)
        self._move_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        self._move_marker.setIconSize(10)
        self._move_marker.setPenWidth(3)

        self.reset()

    def set_snap_geometry(self, geom: QgsGeometry):
        '''
        snap lines to outline of given geometry

        Parameters
        ----------
        snap_geometry : QgsGeometry
            geometry to snap lines to
        '''
        if not geom:
            return
        if SHAPELY_LOADED:
            self.snap_geometry = wkt.loads(geom.asWkt()).boundary
        # alternative for MacOS
        else:
            self.snap_geometry = QgsCurvePolygon()
            self.snap_geometry.fromWkt(geom.asWkt())

    def reset(self):
        '''
        reset drawing
        '''
        scene = self.canvas.scene()
        if self.draw_markers:
            for m in self.markers:
                scene.removeItem(m)
            self.markers = []
        self._moving = False
        self._drawing = False
        self.rubberband.reset(self.wkbtype)

    def canvasDoubleClickEvent(self, e):
        '''
        override, emit line on double click
        '''
        if self._moving:
            self.rubberband.removeLastPoint()
        geom = self.rubberband.asGeometry()
        self.drawn.emit(self.transform_from_map(geom))
        self.reset()

    def _snap(self, point: QgsPoint) -> QgsPointXY:
        '''
        snap point to snap-geometry
        '''
        point = self.transform_from_map(point)
        if SHAPELY_LOADED:
            p = geometry.Point(point.x(), point.y())
            np = nearest_points(self.snap_geometry, p)[0]
            p = QgsPointXY(np.x, np.y)
        # alternative for MacOS
        else:
            closest = QgsGeometryUtils.closestPoint(
                self.snap_geometry, QgsPoint(point.x(), point.y()))
            p = QgsPointXY(closest.x(), closest.y())
        p = self.transform_to_map(p)
        return p

    def canvasPressEvent(self, e):
        '''
        override, finish line segment when map is clicked
        '''
        if(e.button() == Qt.RightButton):
            if self._moving:
                self.rubberband.removeLastPoint()
            geom = self.rubberband.asGeometry()
            self.drawn.emit(self.transform_from_map(geom))
            self.reset()
            return
        self._moving = False
        self._drawing = True
        point = self.toMapCoordinates(e.pos())
        if self.snap_geometry:
            point = self._snap(point)
        self.rubberband.addPoint(point, True)
        if self.draw_markers:
            marker = QgsVertexMarker(self.canvas)
            marker.setCenter(point)
            marker.setColor(self.color)
            marker.setIconSize(8)
            marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            marker.setPenWidth(4)
            self.markers.append(marker)

    def canvasMoveEvent(self, e):
        '''
        override, draw connecting line to last segment when moving mouse
        '''
        if not self.snap_geometry and not self._drawing:
            return
        point = self.toMapCoordinates(e.pos())
        if self.snap_geometry:
            point = self._snap(point)
        if self.snap_geometry:
            self._move_marker.setCenter(point)
        if self._drawing:
            #self.rubberBand.removeLastPoint()
            if self._moving:
                self.rubberband.removeLastPoint()
            self.rubberband.addPoint(point, True)
            self._moving = True

    def disconnect(self, **kwargs):
        '''
        override, 'remove' marker
        '''
        if self._move_marker:
            #scene = self.canvas.scene()
            #scene.removeItem(self._move_marker)
            # workaround: if removed from scene marker won't appear any more
            # set it somewhere it can't be seen
            self._move_marker.setCenter(QgsPointXY(0, 0))
        super().disconnect(**kwargs)

class PolygonMapTool(LineMapTool):
    '''
    draw a polygon on the map

    Attributes
    ----------
    drawn : pyqtSignal
        emitted after double click or right click on the map canvas, emits the
        drawn polygon
    '''
    wkbtype = QgsWkbTypes.PolygonGeometry