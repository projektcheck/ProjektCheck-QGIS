from pctools.base import Geopackage
from pctools.base import settings

import os

base_path = os.path.dirname(os.path.realpath(__file__))

settings.EPSG = 25832 # epsg in database
settings.MAX_AREA_DISTANCE = 1000
settings.GOOGLE_API_KEY = 'AIzaSyDL32xzaNsQmB_fZGU9SF_FtnvJ4ZrwP8g'
settings.BASE_PATH = base_path
settings.TEMPLATE_PATH = os.path.join(base_path, 'templates')
settings.BASEDATA = Geopackage(base_path=os.path.join(base_path, 'data'),
                               read_only=True)
