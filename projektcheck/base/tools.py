from qgis import utils
from qgis.PyQt.QtCore import pyqtSignal, Qt, QTimer
from qgis.PyQt.QtGui import QCursor
from qgis.gui import QgsMapToolEmitPoint, QgsMapToolIdentify
from qgis.PyQt.QtWidgets import QToolTip
from qgis.core import (QgsVectorLayer, QgsFeature, QgsCoordinateTransform,
                       QgsProject, QgsCoordinateReferenceSystem, QgsGeometry)


class MapTool:
    '''
    abstract class for tools triggered by clicking a certain ui element
    '''
    cursor = QCursor(Qt.CrossCursor)

    def __init__(self, ui_element, tip='', canvas=None):
        self.ui_element = ui_element
        self.canvas = canvas or utils.iface.mapCanvas()
        self.ui_element.clicked.connect(self.toggle)
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


class FeaturePicker(MapTool, QgsMapToolIdentify):
    feature_picked = pyqtSignal(QgsVectorLayer, QgsFeature)

    def __init__(self, ui_element, canvas=None):
        MapTool.__init__(self, ui_element, canvas=canvas)
        QgsMapToolIdentify.__init__(self, canvas=self.canvas)

    def canvasReleaseEvent(self, mouseEvent):
        results = self.identify(mouseEvent.x(), mouseEvent.y(),
                                self.LayerSelection, self.VectorLayer)
        if len(results) > 0:
            self.feature_picked.emit(results[0].mLayer,
                                    QgsFeature(results[0].mFeature))


class DrawingTool(MapTool):
    '''
    abstract class for tools drawing on the canvas
    '''

    def draw(self, canvas):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def run(self):
        pass


