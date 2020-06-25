from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject, QgsSymbol,
                       QgsSimpleFillSymbolLayer, QgsRectangle,
                       QgsRendererCategory, QgsCategorizedSymbolRenderer,
                       QgsVectorLayer, QgsPointXY)
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QToolBox, QLayout
import os
import sys
import subprocess
import pandas as pd
import functools
import threading
from typing import Tuple, Union, List

from projektchecktools.base.database import FeatureCollection, Database, Feature
from settings import settings

def interpolate(start: float, end: float, step: float, n_steps: float) -> float:
    ''' interpolate a value between start and end value '''
    return (end - start) * step / n_steps + start

def set_category_renderer(layer: QgsVectorLayer, column: str,
                          start_color: Tuple[int, int, int],
                          end_color: Tuple[int, int, int], unit: str = ''):
    '''
    apply a category renderer to a layer. The categories will be the unique
    values of the given column with interpolated colors between given start
    and end color

    Parameters
    ----------
    layer : QgsVectorLayer
        layer to apply the renderer to
    column : str
        name of the column containing the categories
    start_color : tuple
        rgb values of the first color in the color range
    end_color : tuple
        rgb values of the last color in the color range
    unit : str
        a unit to be added to the category label, defaults to no unit
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

def center_canvas(canvas: QgsMapCanvas, point: QgsPointXY,
                  crs: QgsCoordinateReferenceSystem = None):
    '''
    center canvas on point

    Parameters
    ----------
    canvas : QgsMapCanvas
        the map to center
    point : QgsPointXY
        point with coordinates to center the map on
    crs : QgsCoordinateReferenceSystem
        projection the point is in, defaults to the crs of the map
    '''
    rect = QgsRectangle(point, point)
    if crs:
        transform = QgsCoordinateTransform(
            crs,
            canvas.mapSettings().destinationCrs(),
            QgsProject.instance()
        )
    canvas.setExtent(transform.transform(rect))
    canvas.refresh()

def add_selection_icons(toolbox: QToolBox):
    '''
    apply icons showing the toggle state to a toolbox
    (actually imitating a QgsCollabsibleGroupBox)
    '''
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

def get_ags(features: Union[List[Feature], FeatureCollection],
            basedata: Database, source_crs: QgsCoordinateReferenceSystem = None,
            use_centroid: bool = False) -> List[Feature]:
    """
    get the ags entries the given QGIS Features are in

    Parameters
    ----------
    feature : list or FeatureCollection
        the features to get ags for
    basedata : Database
        the database containing the wokspace 'Basisdaten_deutschland' with
        the table 'bkg_gemeinden'
    source_crs : QgsCoordinateReferenceSystem
        crs of the feature geometries
    use_centroid : bool, optional
        use centroid of features to get area with ags only, defaults using the
        whole geometry of each feature

    Returns
    -------
    list
        list of ags-features the given features are in (same length and order)

    Raises
    ------
    Exception
        one of the features is within multiple communities or in none
    """
    workspace = basedata.get_workspace('Basisdaten_deutschland')
    ags_table = workspace.get_table('bkg_gemeinden')

    target_crs = QgsCoordinateReferenceSystem(settings.EPSG)

    ags_feats = []

    for feat in features:
        geom = feat.geom if hasattr(feat, 'geom') else feat.geometry()
        if source_crs:
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

def clear_layout(layout: QLayout):
    '''
    empties layout by removing children and grand-children (complete hierarchy)
    of the layout recursively

    Parameters
    ----------
    layout : QLayout
        the layout to empty
    '''
    while layout.count():
        child = layout.takeAt(0)
        if not child:
            continue
        if child.widget():
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())

def round_df_to(df: pd.DataFrame, rounding_factor: int) -> pd.DataFrame:
    """
    Round all values of a Dataframe to some value.
    For example: round to 5 euro

    Parameters
    ----------
    df : Dataframe
        the input dataframe
    rounding_factor : int
        rounding value

    Returns
    -------
    DataFrame
    """
    df = df / rounding_factor
    df = df.apply(pd.Series.round)
    df *= rounding_factor
    df = df.astype('int')
    return df

def threaded(function):
    '''
    wrapper for a function to execute it in a thread
    '''
    @functools.wraps(function)
    def _threaded(*args, **kwargs):
        thread = threading.Thread(target=function, args=args, kwargs=kwargs)
        thread.start()
        thread.join()
    return _threaded

def open_file(path: str):
    '''
    open a file with the standard program of the OS

    Parameters
    ----------
    path : str
        full path to file
    '''
    if sys.platform == 'win32':
        threaded(os.startfile)(path)
    else:
        opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
        subprocess.call([opener, path])
