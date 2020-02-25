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
        self.layername = layername
        self.data_path = data_path
        self.layer = None
        self._l = None
        self.groupname = groupname
        self.prepend = prepend

    @property
    def root(self):
        root = QgsProject.instance().layerTreeRoot()
        if self.groupname:
            root = Layer.add_group(self.groupname, prepend=self.prepend)
        return root

    @property
    def tree_layer(self):
        if not self.layer:
            return None
        return self.root.findLayer(self.layer)

    @classmethod
    def add_group(self, groupname, prepend=True):
        groupnames = groupname.split('/')
        root = QgsProject.instance().layerTreeRoot()
        group = nest_groups(root, groupnames, prepend=prepend)
        return group

    @classmethod
    def find(self, label, groupname=''):
        root = QgsProject.instance().layerTreeRoot()
        if groupname:
            groupnames = groupname.split('/')
            while groupnames:
                g = groupnames.pop(0)
                root = root.findGroup(g)
                if not root:
                    return

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
             filter=None, expanded=True, prepend=False):
        try:
            if not self.layer:
                layers = Layer.find(label, groupname=self.groupname)
                if layers:
                    self.layer = layers[0].layer()
        except:
            self.layer = None
        if redraw:
            self.remove()

        if not self.layer:
            self.layer = QgsVectorLayer(self.data_path, self.layername, "ogr")
            if label:
                self.layer.setName(label)
            QgsProject.instance().addMapLayer(self.layer, False)
            self.layer.loadNamedStyle(style_path)
        tree_layer = self.tree_layer
        if not tree_layer:
            tree_layer = self.root.insertLayer(0, self.layer) if prepend else\
                self.root.addLayer(self.layer)
        tree_layer.setItemVisibilityChecked(checked)
        tree_layer.setExpanded(expanded)
        if filter is not None:
            self.layer.setSubsetString(filter)
        return self.layer

    def set_visibility(self, state):
        tree_layer = self.tree_layer
        if tree_layer:
            tree_layer.setItemVisibilityChecked(state)

    def zoom_to(self):
        if not self.layer:
            return
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
