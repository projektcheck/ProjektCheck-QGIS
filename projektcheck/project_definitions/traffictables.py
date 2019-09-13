from projektcheck.base import ProjectTable, Field


class TrafficConnector(ProjectTable):

    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')

    class Meta:
        workspace = 'traffic'


