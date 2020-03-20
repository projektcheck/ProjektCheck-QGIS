from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class ApProJahr(ProjectTable):

    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')
    jahr = Field(int, 0)
    arbeitsplaetze = Field(int, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'


class WohnenStruktur(ProjectTable):

    id_teilflaeche = Field(int, 0)
    jahr = Field(int, 0)
    alter_we = Field(int, 0)
    id_gebaeudetyp = Field(int, 0)
    wohnungen = Field(float, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'


class WohnenProJahr(ProjectTable):

    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')
    jahr = Field(int, 0)
    id_altersklasse = Field(int, 0)
    altersklasse = Field(str, '')
    bewohner = Field(float, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'
