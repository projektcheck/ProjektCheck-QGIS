from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject, QgsSymbol,
                       QgsSimpleFillSymbolLayer, QgsRectangle,
                       QgsRendererCategory, QgsCategorizedSymbolRenderer)
from qgis.PyQt.QtGui import QIcon
import os
import sys
import subprocess
import pandas as pd
import functools
import threading

from settings import settings

def interpolate(start, end, step, n_steps):
    return (end - start) * step / n_steps + start

def set_category_renderer(layer, column, start_color, end_color,
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
    layer.setRenderer(renderer)

def center_canvas(canvas, point, crs=None):
    rect = QgsRectangle(point, point)
    if crs:
        transform = QgsCoordinateTransform(
            crs,
            canvas.mapSettings().destinationCrs(),
            QgsProject.instance()
        )
    canvas.setExtent(transform.transform(rect))
    canvas.refresh()

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

def get_ags(features, basedata, source_crs=None, use_centroid=False):
    """
    get the ags entry of the geometries of the given QGIS Features

    Parameters
    ----------
    feature : QgsFeature
        a feature table
    basedata : Database
        the database containing the wokspace 'Basisdaten_deutschland' with
        the table 'bkg_gemeinden'
    source_crs : int
        epsg code of the feature geometries
    use_centroid : bool, optional
        if True - use centroid of features to get area with ags
        if False - use whole geometry of features
        defaults to False

    Returns
    -------
    ags : list of Feature

    Raises
    ------
    Exception
        feature is within multiple communities or in none
    """
    workspace = basedata.get_workspace('Basisdaten_deutschland')
    ags_table = workspace.get_table('bkg_gemeinden')

    target_crs = QgsCoordinateReferenceSystem(settings.EPSG)

    ags_feats = []

    for feat in features:
        geom = feat.geom if hasattr(feat, 'geom') else feat.geometry()
        if (source_crs):
            tr = QgsCoordinateTransform(
                source_crs, target_crs, QgsProject.instance())
            geom.transform(tr)
        wkt = geom.centroid().asWkt() if use_centroid else geom.asWkt()
        ags_table.spatial_filter(wkt)
        if len(ags_table) < 1:
            raise Exception(f'Feature {feat.id()} liegt nicht in Deutschland.')
        if len(ags_table) > 1:
            raise Exception(
                f'Feature {feat.id()} wurde mehreren Gemeinden zugeordnet.')
        ags_feats.append(list(ags_table.features())[0])
    return ags_feats

def clear_layout(layout):
    while layout.count():
        child = layout.takeAt(0)
        if not child:
            continue
        if child.widget():
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())

def round_df_to(df, rounding_factor):
    """
    Round all values of a Dataframe to some value.
    For example: round to 5 euro

    Parameters
    ----------
    df : pandas dataframe
        the input dataframe
    rounding_factor : int
        rounding value

    """
    df = df / rounding_factor
    df = df.apply(pd.Series.round)
    df *= rounding_factor
    df = df.astype('int')
    return df

def threaded(function):
    @functools.wraps(function)
    def _threaded(*args, **kwargs):
        thread = threading.Thread(target=function, args=args, kwargs=kwargs)
        thread.start()
        thread.join()
    return _threaded

def open_file(path):
    if sys.platform == 'win32':
        threaded(os.startfile)(path)
    else:
        opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
        subprocess.call([opener, path])
