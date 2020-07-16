from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class Connectors(ProjectTable):
    id_teilflaeche = Field(int, 0)
    name_teilflaeche = Field(str, '')

    class Meta:
        workspace = 'traffic'


class Ways(ProjectTable):
    nutzungsart = Field(int, 0)
    miv_anteil = Field(float, 0)
    wege_gesamt = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class WeightedLinks(ProjectTable):
    weight = Field(float, 0)

    class Meta:
        workspace = 'traffic'


class Links(ProjectTable):
    weight = Field(float, 0)
    from_node_id = Field(int, 0)
    to_node_id = Field(int, 0)


class Itineraries(ProjectTable):
    transfer_node_id = Field(int, 0)
    route_id = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class Routes(ProjectTable):
    node_ids = Field(str, '')
    source_id = Field(int, 0)

    class Meta:
        workspace = 'traffic'


class Nodes(ProjectTable):

    class Meta:
        workspace = 'traffic'


class TransferNodes(ProjectTable):
    node_id = Field(int, 0)
    weight = Field(float, 0)
    name = Field(str, '')

    class Meta:
        workspace = 'traffic'



