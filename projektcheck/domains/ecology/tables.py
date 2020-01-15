from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class BodenbedeckungNullfall(ProjectTable):

    IDBodenbedeckung = Field(int, 0)

    class Meta:
        workspace = 'oekologie'


class BodenbedeckungPlanfall(ProjectTable):

    IDBodenbedeckung = Field(int, 0)

    class Meta:
        workspace = 'oekologie'


class BodenbedeckungAnteile(ProjectTable):

    IDBodenbedeckung = Field(int, 0)
    planfall = Field(bool, True)
    anteil = Field(float, 0)

    class Meta:
        workspace = 'oekologie'
