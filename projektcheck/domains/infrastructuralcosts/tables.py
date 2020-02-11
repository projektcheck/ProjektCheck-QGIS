from projektcheck.base.project import ProjectTable
from projektcheck.base.database import Field


class ErschliessungsnetzLinien(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    length = Field(float, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class ErschliessungsnetzPunkte(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    bezeichnung = Field(str, '')
    Euro_EH = Field(float, 0)
    Euro_EN = Field(float, 0)
    Cent_BU = Field(int, 0)
    Lebensdauer = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class KostenkennwerteLinienelemente(ProjectTable):
    IDNetz = Field(int, 0)
    IDNetzelement = Field(int, 0)
    Euro_EH = Field(float, 0)
    Euro_EN = Field(float, 0)
    Cent_BU = Field(int, 0)
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


class Kostenaufteilung(ProjectTable):
    IDNetz = Field(int, 0)
    IDKostenphase = Field(int, 0)
    Anteil_GSB = Field(int, 0)
    Anteil_GEM = Field(int, 0)
    Anteil_ALL = Field(int, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'


class GesamtkostenTraeger(ProjectTable):
    IDNetz = Field(int, 0)
    Netz = Field(str, '')
    Betrag_GSB = Field(float, 0)
    Betrag_GEM = Field(float, 0)
    Betrag_ALL = Field(float, 0)

    class Meta:
        workspace = 'infrastukturfolgekosten'

