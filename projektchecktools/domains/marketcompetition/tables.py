from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class Centers(ProjectTable):

    name = Field(str, '')
    nutzerdefiniert = Field(int, -1)
    umsatz_differenz = Field(int, 0)
    umsatz_planfall = Field(int, 0)
    umsatz_nullfall = Field(int, 0)
    auswahl = Field(int, 0)
    ags = Field(str, '')
    rs = Field(str, '')

    class Meta:
        workspace = 'marketcompetition'



