from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


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
    name = Field(str, '')
    berechnet = Field(str, '')

    class Meta:
        workspace = 'erreichbarkeiten'


class ErreichbarkeitenOEPNV(ProjectTable):

    id_origin = Field(int, 0)
    id_destination = Field(int, 0)
    verkehrsmittel = Field(str, '')
    abfahrt = Field(str, '')
    umstiege = Field(int, 0)
    ziel = Field(str, '')
    dauer = Field(str, '')

    class Meta:
        workspace = 'erreichbarkeiten'


class Einrichtungen(ProjectTable):

    projektcheck_category = Field(str, '')
    name = Field(str, '')

    class Meta:
        workspace = 'erreichbarkeiten'


class Isochronen(ProjectTable):

    sekunden = Field(int, 0)
    minuten = Field(float, 0)
    modus = Field(str, '')
    id_connector = Field(int, 0)

    class Meta:
        workspace = 'erreichbarkeiten'
