from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class ErschliessungsnetzLinien(ProjectTable):
    IDNetzelement = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class ErschliessungsnetzPunkte(ProjectTable):
    IDNetzelement = Field(int, 0)
    bezeichnung = Field(str, '')
    euro_EH = Field(float, 0)
    euro_EN = Field(float, 0)
    cent_BU = Field(float, 0)
    lebensdauer = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'