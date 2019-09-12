from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform, QgsProject)
                       #QgsVectorLayer, QgsApplication, QgsSpatialIndex)
from collections import OrderedDict

from settings import settings

def get_ags(features, source_crs=None):
    """
    get the ags and names of the areas the centroids of all polygons in given
    feature table or layer lie in, the bkg_gemeinden table is taken as a source
    for ags and names

    Parameters
    ----------
    feature : QgsFeature
        a feature table

    Returns
    -------
    ags : str
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

    ags = []

    for feat in features:
        geom = feat.geometry()
        if (source_crs):
            tr = QgsCoordinateTransform(
                source_crs, target_crs, QgsProject.instance())
            geom.transform(tr)
        ags_table.spatial_filter(geom.asWkt())
        if len(ags_table) < 1:
            raise Exception(f'Feature {feat.id} liegt nicht in Deutschland.')
        if len(ags_table) > 1:
            raise Exception(
                f'Feature {feat.id} wurde mehreren Gemeinden zugeordnet.')
        ags.append(list(ags_table.features())[0].AGS)
    return ags

