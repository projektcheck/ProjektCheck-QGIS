from projektcheck.domains.definitions.tables import Projektrahmendaten
from projektcheck.domains.reachabilities.tables import Einrichtungen
from projektcheck.domains.reachabilities.geoserver_query import GeoserverQuery
from projektcheck.base.domain import Worker


class EinrichtungenQuery(Worker):

    _param_projectname = 'projectname'
    _workspace = 'FGDB_Erreichbarkeit.gdb'
    cutoff = None

    categories = [u'Kita', u'Autobahnanschlussstelle', u'Dienstleistungen',
                  u'Ärzte', 'Freizeit', u'Läden',
                  u'Supermarkt/Einkaufszentrum', 'Schule']

    def __init__(self, project, radius=1, parent=None):
        super().__init__(parent=parent)
        self.einrichtungen = Einrichtungen.features(project=project)
        self.project_frame = Projektrahmendaten.features(project=project)[0]
        self.radius = radius

    def run(self):
        query = GeoserverQuery()
        radius = self.par.radius.value * 1000
        centroid = self.project_frame.geom.asPoint()
        target_epsg = self.parent_tbx.config.epsg
        arcpy.AddMessage('Frage Geoserver an...')
        features = query.get_features(centroid, radius,
                                      self.categories, target_epsg)
        arcpy.AddMessage('Schreibe {} Einrichtungen in die Datenbank...'
                         .format(len(features)))
        self.parent_tbx.delete_rows_in_table('Einrichtungen')
        column_values = {'name': [], 'SHAPE': [], 'projektcheck_category': []}
        for feat in features:
            column_values['name'].append(feat.name)
            feat.create_geom()
            column_values['SHAPE'].append(feat.geom)
            column_values['projektcheck_category'].append(feat.category)

        self.parent_tbx.insert_rows_in_table('Einrichtungen', column_values)
