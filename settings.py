'''
Basic settings of the plugin. Change but do not remove any of these properties!
'''

from projektchecktools.base.project import settings

import os

base_path = os.path.dirname(os.path.realpath(__file__))

settings.EPSG = 25832 # epsg in database
settings.MAX_AREA_DISTANCE = 1000
settings.BASE_PATH = base_path
settings.MAX_AREA_DISTANCE = 1000
settings.BASE_PATH = base_path
settings.TEMPLATE_PATH = os.path.join(base_path, 'templates')
settings.IMAGE_PATH = os.path.join(base_path, 'images')
settings.HELP_PATH = os.path.join(base_path, 'projektchecktools', 'help')
settings.BASEDATA_URL = 'https://gis.ggr-planung.de/repos/projektcheck'
settings.GEOSERVER_URL = 'https://geoserver.ggr-planung.de/geoserver/projektcheck'
# name of zenus raster file in basedata
settings.ZENSUS_500_FILE = 'ZensusEinwohner500.tif'
settings.ZENSUS_100_FILE = 'ZensusEinwohner100.tif'
settings.DEBUG = True
settings.PROJECT_RADIUS = 20000
