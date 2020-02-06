from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class ErschliessungsnetzLinien(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class ErschliessungsnetzPunkte(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    bezeichnung = Field(str, '')
    Euro_EH = Field(float, 0)
    Euro_EN = Field(float, 0)
    Cent_BU = Field(float, 0)
    Lebensdauer = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class KostenkennwerteLinienelemente(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    Euro_EH = Field(float, 0)
    Euro_EN = Field(float, 0)
    Cent_BU = Field(float, 0)
    Lebensdauer = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class Gesamtkosten(ProjectTable):
    IDNetz = Field(int, 0)
    Netz = Field(str, '')
    IDKostenphase = Field(int, 0)
    Kostenphase = Field(str, '')
    Euro = Field(float, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'
