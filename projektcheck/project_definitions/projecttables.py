from projektcheck.base import ProjectTable, Field


class Areas(ProjectTable):

    nutzungsart = Field(int, 0)
    name = Field(str, 0)
    aufsiedlungsdauer = Field(int, 0)
    validiert = Field(int, 0)
    beginn_nutzung = Field(int, 0)
    ags_bkg = Field(int, 0)
    gemeinde_name = Field(int, 0)
    we_gesamt = Field(int, 0)
    ap_gesamt = Field(int, 0)
    vf_gesamt = Field(int, 0)
    ew = Field(int, 0)
    wege_gesamt = Field(int, 0)
    wege_miv = Field(int, 0)

    class Meta:
        workspace = 'project_definitions'
