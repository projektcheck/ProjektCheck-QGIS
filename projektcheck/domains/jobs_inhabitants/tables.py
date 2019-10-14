from projektcheck.base import ProjectTable, Field, settings


class ApProJahr(ProjectTable):

    id_teilflaeche = Field(int, 0)
    jahr = Field(int, 0)
    arbeitsplaetze = Field(int, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'


class Branchenanteile(ProjectTable):

    id_teilflaeche = Field(int, 0)
    id_branche = Field(int, 0)
    anteil = Field(float, 0)

    class Meta:
        workspace = 'bewohner_arbeitsplaetze'
