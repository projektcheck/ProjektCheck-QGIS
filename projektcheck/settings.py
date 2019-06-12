from pctools.backend import Geopackage
from pctools.base import settings

settings.EPSG = 31467 # epsg in database
settings.MAX_AREA_DISTANCE = 1000
settings.GOOGLE_API_KEY = 'AIzaSyDL32xzaNsQmB_fZGU9SF_FtnvJ4ZrwP8g'

database = Geopackage()
database.add_workspace('Basedata', 'Basisdaten_Deutschland.gpk', is_base=True)
database.add_workspace('Definition', 'Definition_Projekt.gpk', is_base=False)

settings.DATABASE = database
