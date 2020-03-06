from projektchecktools.base.geopackage import Geopackage
from projektchecktools.base.project import settings

import os

base_path = os.path.dirname(os.path.realpath(__file__))

settings.EPSG = 25832 # epsg in database
settings.MAX_AREA_DISTANCE = 1000
settings.GOOGLE_API_KEY = 'AIzaSyDL32xzaNsQmB_fZGU9SF_FtnvJ4ZrwP8g'
settings.BASE_PATH = base_path
settings.MAX_AREA_DISTANCE = 1000
settings.BASE_PATH = base_path
settings.TEMPLATE_PATH = os.path.join(base_path, 'templates')
settings.IMAGE_PATH = os.path.join(base_path, 'images')
settings.TEMP_PATH = os.path.join(base_path, 'data', 'temp')
settings.HELP_PATH = os.path.join(base_path, 'projektchecktools', 'help')
#settings.BASEDATA = Geopackage(base_path=os.path.join(base_path, 'data'),
                               #read_only=True)
settings.BASEDATA_URL = 'https://gis.ggr-planung.de/repos/projektcheck'
settings.DEBUG = True
settings.PROJECT_RADIUS = 20000
