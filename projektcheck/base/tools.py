from qgis import utils
from qgis.PyQt.QtCore import pyqtSignal, Qt, QTimer
from qgis.PyQt.QtGui import QCursor, QColor
from qgis.gui import (QgsMapToolEmitPoint, QgsMapToolIdentify, QgsRubberBand,
                      QgsVertexMarker)
from qgis.PyQt.QtWidgets import QToolTip
from qgis.core import (QgsFeature, QgsCoordinateTransform,
                       QgsProject, QgsCoordinateReferenceSystem, QgsGeometry,
                       QgsPointXY, QgsWkbTypes)


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
                 line_width=2, line_style=Qt.SolidLine):
        self.canvas = canvas
        MapTool.__init__(self, ui_element, self.canvas)
        QgsMapToolEmitPoint.__init__(self, canvas=self.canvas)
        self.rubberband = QgsRubberBand(self.canvas,
                                           self.wkbtype)
        color = QColor(color) if color else QColor(0, 0, 255)
        self.rubberband.setColor(color)
        color.setAlpha(100)
        self.rubberband.setFillColor(color)
        self.rubberband.setLineStyle(line_style)
        self.rubberband.setWidth(line_width)

        self.draw_markers = draw_markers
        if self.draw_markers:
            # auto points on outline should but doesn't work:
            #self.drawing_lines.setIcon(QgsRubberBand.ICON_CIRCLE)
            #self.drawing_lines.setIconSize(8)

            # drawing markers manually instead
            self.markers = []

        self._drawing = False
        self._moving =  False
        self.reset()

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

    def canvasPressEvent(self, e):
        if(e.button() == Qt.RightButton):
            if self._moving:
                self.rubberband.removeLastPoint()
            self.drawn.emit(self.rubberband.asGeometry())
            self.reset()
            return
        self._moving = False
        self._drawing = True
        point = self.toMapCoordinates(e.pos())
        point = QgsPointXY(point.x(), point.y())
        self.rubberband.addPoint(point, True)
        if self.draw_markers:
            marker = QgsVertexMarker(self.canvas)
            marker.setCenter(point)
            marker.setColor(Qt.blue)
            marker.setIconSize(8)
            marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            marker.setPenWidth(4)
            self.markers.append(marker)

    def canvasMoveEvent(self, e):
        if self._drawing:
            #self.rubberBand.removeLastPoint()
            if self._moving:
                self.rubberband.removeLastPoint()
            point = self.toMapCoordinates(e.pos())
            point = QgsPointXY(point.x(), point.y())
            self.rubberband.addPoint(point, True)
            self._moving = True


class PolygonMapTool(LineMapTool):
    wkbtype = QgsWkbTypes.PolygonGeometry