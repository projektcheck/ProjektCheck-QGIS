'''
Basic settings of the plugin. You may change but not remove any of these properties!
'''
import os

from projektcheck.base.project import settings

settings.EPSG = 25832 # epsg in database
settings.MAX_AREA_DISTANCE = 1000 # max distance between project areas
settings.PROJECT_RADIUS = 20000 # size of selectable study area around the project areas

# paths to resources
base_path = os.path.dirname(os.path.realpath(__file__))
settings.BASE_PATH = base_path
settings.TEMPLATE_PATH = os.path.join(base_path, 'templates')
settings.IMAGE_PATH = os.path.join(base_path, 'images')
settings.HELP_PATH = os.path.join(base_path, 'help')
settings.UI_PATH = os.path.join(base_path, 'ui')

# service urls
settings.BASEDATA_URL = 'https://projektcheck.dl.ils-geomonitoring.de/downloads'
settings.GEOSERVER_URL = 'https://projektcheck.gs.ils-geomonitoring.de/projektcheck'
settings.OTP_ROUTER_URL = 'https://otp.ggr.ils-geomonitoring.de/otp'
settings.OTP_ROUTER_ID = 'deutschland' # name of the otp router (equals server folder to graph)

# zensus raster files
settings.ZENSUS_500_FILE = 'ZensusEinwohner500.tif'
settings.ZENSUS_100_FILE = 'ZensusEinwohner100.tif'

settings.DEBUG = True
