from projektchecktools.base.project import ProjectTable
from projektchecktools.base.database import Field


class Gemeinden(ProjectTable):
    RS = Field(str, )
    AGS = Field(str, )
    GEN = Field(str, )
    BEZ = Field(str, )
    IBZ = Field(float, 0)
    BEM = Field(str, )
    Einwohner = Field(int, 0)
    SvB = Field(int, 0)
    SvB_pro_Ew = Field(float, 0)
    Hebesatz_GewSt = Field(int, 0)

    class Meta:
        workspace = 'einnahmen'


class EinwohnerWanderung(ProjectTable):
    AGS = Field(str, '')
    zuzug = Field(float, 0)
    fortzug = Field(float, 0)
    saldo = Field(float, 0)
    fixed = Field(bool, False)
    wanderungs_anteil = Field(float, 0)

    class Meta:
        workspace = 'einnahmen'