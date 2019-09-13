from abc import ABC
from qgis.core import QgsProject, QgsVectorLayer


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

    def __init__(self, layername, data_path, groupname=''):
        self.root = QgsProject.instance().layerTreeRoot()
        self.layername = layername
        self.data_path = data_path
        if groupname:
            group = self.root.findGroup(groupname)
            if not group:
                group = self.root.addGroup(groupname)
            self.root = group

    def draw(self, style_path=None, label=''):
        label = label or self.layername
        layer = QgsVectorLayer(self.data_path, self.layername, "ogr")
        QgsProject.instance().addMapLayer(layer, False)
        layer.loadNamedStyle(style_path)
        self.root.addLayer(layer)

