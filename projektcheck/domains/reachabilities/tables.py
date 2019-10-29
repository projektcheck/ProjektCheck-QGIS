from projektcheck.base import ProjectTable, Field, settings


class ZentraleOrte(ProjectTable):

    id_haltestelle = Field(int, 0)
    id_zentraler_ort = Field(int, 0)
    name = Field(str, '')

    class Meta:
        workspace = 'erreichbarkeiten'


class Haltestellen(ProjectTable):

    abfahrten = Field(int, 0)
    id_bahn = Field(int, 0)
    flaechenzugehoerig = Field(bool, False)

    class Meta:
        workspace = 'erreichbarkeiten'