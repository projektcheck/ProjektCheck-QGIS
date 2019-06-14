from pctools.backend import Geopackage
from pctools.base import settings

import os

base_path = os.path.dirname(os.path.realpath(__file__))

settings.EPSG = 31467 # epsg in database
settings.MAX_AREA_DISTANCE = 1000
settings.GOOGLE_API_KEY = 'AIzaSyDL32xzaNsQmB_fZGU9SF_FtnvJ4ZrwP8g'
settings.BASE_PATH = base_path
settings.BASEDATA_PATH = os.path.join(base_path, 'data')
settings.TEMPLATE_PATH = os.path.join(base_path, 'templates')
