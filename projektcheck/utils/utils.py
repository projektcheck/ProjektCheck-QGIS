from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject, QgsSymbol,
                       QgsSimpleFillSymbolLayer,
                       QgsRendererCategory, QgsCategorizedSymbolRenderer)
from qgis.PyQt.QtGui import QIcon, QColor
                       #QgsVectorLayer, QgsApplication, QgsSpatialIndex)
from collections import OrderedDict
import os

from settings import settings

def interpolate(start, end, step, n_steps):
    return (end - start) * step / n_steps + start

def category_renderer(layer, column, start_color, end_color,
                      unit=''):
    '''
    colors - rgb tuple
    '''
    idx = layer.fields().indexOf(column)
    unique_values = list(layer.uniqueValues(idx))
    unique_values.sort()
    categories = []
    geometry_type = layer.geometryType()
    for i, value in enumerate(unique_values):
        # initialize the default symbol for this geometry type
        symbol = QgsSymbol.defaultSymbol(geometry_type)

        # configure a symbol layer
        layer_style = {}
        rgb = []
        for c in range(3):
            rgb.append(str(int(interpolate(start_color[c], end_color[c],
                                           i, len(unique_values)))))
        layer_style['color'] = ','.join(rgb)
        #layer_style['outline'] = '#000000'
        symbol_layer = QgsSimpleFillSymbolLayer.create(layer_style)

        # replace default symbol layer with the configured one
        if symbol_layer is not None:
            symbol.changeSymbolLayer(0, symbol_layer)

        # create renderer object
        category = QgsRendererCategory(value, symbol, f'{value} {unit}')
        # entry for the list of category items
        categories.append(category)

    # create renderer object
    renderer = QgsCategorizedSymbolRenderer(column, categories)
    return renderer

def add_selection_icons(toolbox):

    triangle_right = QIcon(os.path.join(
        settings.IMAGE_PATH, 'triangle-right.png'))
    triangle_down = QIcon(os.path.join(
        settings.IMAGE_PATH, 'triangle-down.png'))

    def set_closed():
        for i in range(toolbox.count()):
            toolbox.setItemIcon(i, triangle_right)

    def on_select(idx):
        set_closed()
        toolbox.setItemIcon(idx, triangle_down)

    toolbox.currentChanged.connect(on_select)
    on_select(toolbox.currentIndex())

def get_ags(features, source_crs=None):
    """
    get the ags entry of the geometries of the given QGIS Features

    Parameters
    ----------
    feature : QgsFeature
        a feature table
    source_crs : int
        epsg code of the feature geometries

    Returns
    -------
    ags : list of Feature
    """
    basedata = settings.BASEDATA.get_workspace('Basisdaten_deutschland')
    ags_table = basedata.get_table('bkg_gemeinden')
    #gem_layer = QgsVectorLayer(basedata.path, 'bkg_gemeinden', 'ogr')

    #index = QgsSpatialIndex()
    #for feat in features:
        #index.insertFeature(feat)
    #for gem_feat in gem_layer.getFeatures():
        #ids = index.intersects(gem_feat.geometry().centroid())

    target_crs = QgsCoordinateReferenceSystem(settings.EPSG)

    ags_feats = []

    for feat in features:
        geom = feat.geometry()
        if (source_crs):
            tr = QgsCoordinateTransform(
                source_crs, target_crs, QgsProject.instance())
            geom.transform(tr)
        ags_table.spatial_filter(geom.asWkt())
        if len(ags_table) < 1:
            raise Exception(f'Feature {feat.id()} liegt nicht in Deutschland.')
        if len(ags_table) > 1:
            raise Exception(
                f'Feature {feat.id()} wurde mehreren Gemeinden zugeordnet.')
        ags_feats.append(list(ags_table.features())[0])
    return ags_feats

def clearLayout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.layout() is not None:
            clearLayout(child.layout())
