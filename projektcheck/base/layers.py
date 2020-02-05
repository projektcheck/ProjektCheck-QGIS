from abc import ABC
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer
from qgis.utils import iface


def nest_groups(parent, groupnames, prepend=True):
    '''recursively nests groups in order of groupnames'''
    if len(groupnames) == 0:
        return parent
    next_parent = parent.findGroup(groupnames[0])
    if not next_parent:
        next_parent = (parent.insertGroup(0, groupnames[0])
                       if prepend else parent.addGroup(groupnames[0]))
    return nest_groups(next_parent, groupnames[1:], prepend=prepend)


class Layer(ABC):

    def __init__(self, layername, data_path, groupname='', prepend=True):
        self.root = QgsProject.instance().layerTreeRoot()
        self.layername = layername
        self.data_path = data_path
        self.layer = None
        self._l = None
        if groupname:
            groupnames = groupname.split('/')
            group = nest_groups(self.root, groupnames, prepend=prepend)
            self.root = group

    @classmethod
    def find(self, label, groupname=''):
        root = QgsProject.instance().layerTreeRoot()
        if groupname:
            groupnames = groupname.split('/')
            while groupnames:
                g = groupnames.pop()
                root = root.findGroup(g)

        def deep_find(node, label):
            found = []
            if node:
                for child in node.children():
                    if child.name() == label:
                        found.append(child)
                    found.extend(deep_find(child, label))
            return found

        found = deep_find(root, label)
        return found

    def draw(self, style_path=None, label='', redraw=True, checked=True,
             filter=None, expanded=True):
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
            self._l = self.root.addLayer(self.layer)
        self._l.setItemVisibilityChecked(checked)
        self._l.setExpanded(expanded)
        if filter is not None:
            self.layer.setSubsetString(filter)
        return self.layer

    def set_visibility(self, state):
        if self._l:
            self._l.setItemVisibilityChecked(state)

    def zoom_to(self):
        canvas = iface.mapCanvas()
        self.layer.updateExtents()
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
        self.prepend = prepend

    def draw(self, label, checked=True):
        self.layer = None
        for child in self.root.children():
            if child.name() == label:
                self.layer = child.layer()
                break
        if not self.layer:
            self.layer = QgsRasterLayer(self.url, label, 'wms')
            QgsProject.instance().addMapLayer(self.layer, False)
            l = self.root.insertLayer(0, self.layer) if self.prepend \
                else self.root.addLayer(self.layer)
            l.setItemVisibilityChecked(checked)
            l.setExpanded(False)
