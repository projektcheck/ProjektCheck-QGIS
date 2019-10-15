from abc import ABC
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer
from qgis.utils import iface


class Output(ABC):
    '''
    abstract class for visual outputs of tools
    '''

    def draw(self):
        raise NotImplementedError


class Diagram(Output, ABC):
    '''
    abstract class for diagrams
    '''

    def draw(self):
        pass


class Layer(Output):

    def __init__(self, layername, data_path, groupname='', prepend=True):
        self.root = QgsProject.instance().layerTreeRoot()
        self.layername = layername
        self.data_path = data_path
        self.layer = None
        if groupname:
            group = self.root.findGroup(groupname)
            if not group:
                if prepend:
                    group = self.root.insertGroup(0, groupname)
                else:
                    group = self.root.addGroup(groupname)
            self.root = group

    def draw(self, style_path=None, label='', redraw=True, checked=True):
        # ToDo: force redraw (delete and add)
        if not self.layer:
            for child in self.root.children():
                if child.name() == label:
                    self.layer = child.layer()
                    break
        if redraw:
            self.remove()
        if not self.layer:
            self.layer = QgsVectorLayer(self.data_path, self.layername, "ogr")
            if label:
                self.layer.setName(label)
            QgsProject.instance().addMapLayer(self.layer, False)
            self.layer.loadNamedStyle(style_path)
            l = self.root.addLayer(self.layer)
            l.setItemVisibilityChecked(checked)

    def zoom_to(self):
        canvas = iface.mapCanvas()
        canvas.setExtent(self.layer.extent())

    def remove(self):
        if not self.layer:
            return
        QgsProject.instance().removeMapLayer(self.layer.id())
        self.layer = None


class TileLayer(Layer):

    def __init__(self, url, groupname='', prepend=True):
        super().__init__(None, None, groupname=groupname, prepend=prepend)
        self.url = url

    def draw(self, label, checked=True):
        self.layer = None
        for child in self.root.children():
            if child.name() == label:
                self.layer = child.layer()
                break
        if not self.layer:
            self.layer = QgsRasterLayer(self.url, label, 'wms')
            QgsProject.instance().addMapLayer(self.layer, False)
            l = self.root.addLayer(self.layer)
            l.setItemVisibilityChecked(checked)
            l.setExpanded(False)
