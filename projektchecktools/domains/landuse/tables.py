from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class WohnbaulandAnteile(ProjectTable):

    id_teilflaeche = Field(int, 0)
    nettoflaeche = Field(float, 0)

    class Meta:
        workspace = 'definitions'


class WohnflaecheGebaeudetyp(ProjectTable):

    id_teilflaeche = Field(int, 0)
    mean_wohnflaeche = Field(int, 0)
    id_gebaeudetyp = Field(int, 0)
    name_gebaeudetyp = Field(str, 0)

    class Meta:
        workspace = 'definitions'


class GrenzeSiedlungskoerper(ProjectTable):

    class Meta:
        workspace = 'definitions'