from qgis.core import QgsGeometryUtils
from qgis import utils
from qgis.PyQt.QtCore import pyqtSignal, Qt, QTimer
from qgis.PyQt.QtGui import QCursor, QColor
from qgis.gui import (QgsMapToolEmitPoint, QgsMapToolIdentify, QgsRubberBand,
                      QgsVertexMarker)
from qgis.PyQt.QtWidgets import QToolTip
from qgis.core import (QgsFeature, QgsCoordinateTransform, QgsCurvePolygon,
                       QgsProject, QgsCoordinateReferenceSystem, QgsGeometry,
                       QgsPointXY, QgsWkbTypes, QgsPoint)


class MapTool:
    '''
    abstract class for tools triggered by clicking a certain ui element
    '''
    cursor = QCursor(Qt.CrossCursor)

    def __init__(self, ui_element, canvas=None, tip=''):
        self.ui_element = ui_element
        self.canvas = canvas or utils.iface.mapCanvas()
        # workaround: .clicked.connect(self.toggle) works only occasionally
        # reason unknown
        self.ui_element.clicked.connect(lambda x: self.toggle(x))
        self.tip = tip
        if tip:
            self.map_timer = QTimer(self.canvas)
            self.map_timer.timeout.connect(self.show_tip)

    def toggle(self, active):
        if active:
            self.canvas.setMapTool(self)
            self.canvas.mapToolSet.connect(self.disconnect)
            self.canvas.setCursor(self.cursor)
        else:
            self.canvas.unsetMapTool(self)
            self.ui_element.blockSignals(True)
            self.ui_element.setChecked(False)
            self.ui_element.blockSignals(False)

    def disconnect(self, **kwargs):
        self.canvas.mapToolSet.disconnect(self.disconnect)
        self.toggle(False)

    def canvasMoveEvent(self, e):
        if self.tip and self.canvas.underMouse():
            QToolTip.hideText()
            self.map_timer.start(700)

    def show_tip(self):
        if self.canvas.underMouse():
            QToolTip.showText(
                self.canvas.mapToGlobal(self.canvas.mouseLastXY()),
                self.tip, self.canvas)


class MapClickedTool(MapTool, QgsMapToolEmitPoint):
    map_clicked = pyqtSignal(QgsGeometry)

    def __init__(self, ui_element, target_crs=None, canvas=None):
        MapTool.__init__(self, ui_element, canvas=canvas)
        QgsMapToolEmitPoint.__init__(self, canvas=self.canvas)
        self.target_crs = target_crs
        self.canvasClicked.connect(self._map_clicked)

    def _map_clicked(self, point, e):
        geom = QgsGeometry.fromPointXY(point)
        if self.target_crs:
            source_crs = self.canvas.mapSettings().destinationCrs()
            target_crs = QgsCoordinateReferenceSystem(self.target_crs)
            tr = QgsCoordinateTransform(
                source_crs, target_crs, QgsProject.instance())
            geom.transform(tr)
        self.map_clicked.emit(geom)


class FeaturePicker(MapTool, QgsMapToolEmitPoint):
    feature_picked = pyqtSignal(QgsFeature)

    def __init__(self, ui_element, layers=[], canvas=None):
        MapTool.__init__(self, ui_element, canvas=canvas)
        QgsMapToolEmitPoint.__init__(self, canvas=self.canvas)
        self._layers = layers

    def add_layer(self, layer):
        if layer:
            self._layers.append(layer)

    def set_layer(self, layer):
        if not layer:
            self._layers = []
        else:
            self._layers = [layer]

    def canvasReleaseEvent(self, mouseEvent):
        if not self._layers:
            return
        features = QgsMapToolIdentify(self.canvas).identify(
            mouseEvent.x(), mouseEvent.y(), self._layers,
            QgsMapToolIdentify.TopDownStopAtFirst)
        if len(features) > 0:
            self.feature_picked.emit(features[0].mFeature)


class LineMapTool(MapTool, QgsMapToolEmitPoint):
    drawn = pyqtSignal(QgsGeometry)
    wkbtype = QgsWkbTypes.LineGeometry

    def __init__(self, ui_element, canvas=None, color=None, draw_markers=False,
                 line_width=2, line_style=Qt.SolidLine, snap_geometry=None):
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

    def set_snap_geometry(self, geom):
        #if not geom or not SHAPELY_LOADED:
            #return
        #self.snap_geometry = wkt.loads(geom.asWkt()).boundary
        if not geom:
            return
        self.snap_geometry = QgsCurvePolygon()
        self.snap_geometry.fromWkt(geom.asWkt())

    def reset(self):
        scene = self.canvas.scene()
        if self.draw_markers:
            for m in self.markers:
                scene.removeItem(m)
            self.markers = []
        self._moving = False
        self._drawing = False
        self.rubberband.reset(self.wkbtype)

    def canvasDoubleClickEvent(self, e):
        if self._moving:
            self.rubberband.removeLastPoint()
        self.drawn.emit(self.rubberband.asGeometry())
        self.reset()

    def _snap(self, x, y):
        closest = QgsGeometryUtils.closestPoint(
            self.snap_geometry, QgsPoint(x, y))
        return QgsPointXY(closest.x(), closest.y())

    def canvasPressEvent(self, e):
        if(e.button() == Qt.RightButton):
            if self._moving:
                self.rubberband.removeLastPoint()
            self.drawn.emit(self.rubberband.asGeometry())
            self.reset()
            return
        self._moving = False
        self._drawing = True
        p = self.toMapCoordinates(e.pos())
        point = self._snap(p.x(), p.y()) if self.snap_geometry \
            else QgsPointXY(p.x(), p.y())
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
        if not self.snap_geometry and not self._drawing:
            return
        p = self.toMapCoordinates(e.pos())
        point = self._snap(p.x(), p.y()) if self.snap_geometry \
            else QgsPointXY(p.x(), p.y())
        if self.snap_geometry:
            self._move_marker.setCenter(point)
        if self._drawing:
            #self.rubberBand.removeLastPoint()
            if self._moving:
                self.rubberband.removeLastPoint()
            self.rubberband.addPoint(point, True)
            self._moving = True

    def disconnect(self, **kwargs):
        if self._move_marker:
            #scene = self.canvas.scene()
            #scene.removeItem(self._move_marker)
            # workaround: if removed from scene marker won't appear any more
            # set it somewhere it can't be seen
            self._move_marker.setCenter(QgsPointXY(0, 0))
        super().disconnect(**kwargs)

class PolygonMapTool(LineMapTool):
    wkbtype = QgsWkbTypes.PolygonGeometry