from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class TrafficConnector(ProjectTable):

    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')

    class Meta:
        workspace = 'traffic'


