from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class Connectors(ProjectTable):

    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')

    class Meta:
        workspace = 'traffic'


class Links(ProjectTable):
    link_id = Field(int, 0)
    weight = Field(float, 0)
    distance_from_source = Field(float, 0)

    class Meta:
        workspace = 'traffic'


class Nodes(ProjectTable):
    node_id = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class TransferNodes(ProjectTable):
    node_id = Field(int, 0)
    weight = Field(float, 0)
    name = Field(str, '')

    class Meta:
        workspace = 'traffic'



