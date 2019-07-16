from projektcheck.base import ProjectTable, Field


class Areas(ProjectTable):

    id = Field(int, 0)
    id_teilflaeche = Field(int, 0)
    Nutzungsart = Field(int, 0)
    Name = Field(str, 0)
    Aufsiedlungsdauer = Field(int, 0)
    validiert = Field(int, 0)
    Beginn_Nutzung = Field(int, 0)
    ags_bkg = Field(int, 0)
    gemeinde_name = Field(int, 0)
    WE_gesamt = Field(int, 0)
    AP_gesamt = Field(int, 0)
    VF_gesamt = Field(int, 0)
    ew = Field(int, 0)
    Wege_gesamt = Field(int, 0)
    Wege_MIV = Field(int, 0)

    class Meta:
        workspace = 'project_definitions'
