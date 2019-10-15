from projektcheck.base import ProjectTable, Field, settings


class Projektrahmendaten(ProjectTable):
    ags = Field(int, 0)
    gemeinde_name = Field(str, '')
    gemeinde_typ = Field(int, 0)
    projekt_name = Field(str, '')

    class Meta:
        workspace = 'definitions'


class Teilflaechen(ProjectTable):

    nutzungsart = Field(int, 0)
    name = Field(str, '')
    aufsiedlungsdauer = Field(int, 0)
    validiert = Field(int, 0)
    beginn_nutzung = Field(int, 0)

    # actually redundant, but maybe at some point areas might be have
    # different "gemeinden" again
    ags_bkg = Field(str, '')
    gemeinde_typ = Field(int, 0)
    gemeinde_name = Field(str, '')

    we_gesamt = Field(int, 0)
    ap_gesamt = Field(int, 0)
    ap_ist_geschaetzt = Field(bool, True)
    vf_gesamt = Field(int, 0)
    ew = Field(int, 0)
    wege_gesamt = Field(int, 0)
    wege_miv = Field(int, 0)

    class Meta:
        workspace = 'definitions'


class Verkaufsflaechen(ProjectTable):

    id_teilflaeche = Field(int, 0)
    id_sortiment = Field(int, 0)
    name_sortiment = Field(str, '')
    verkaufsflaeche_qm = Field(int, 0)

    class Meta:
        workspace = 'definitions'


class Gewerbeanteile(ProjectTable):

    id_teilflaeche = Field(int, 0)
    id_branche = Field(int, 0)
    name_branche = Field(str, '')
    anteil_definition = Field(int, 0)
    anteil_branche = Field(float, 0)
    anzahl_jobs_schaetzung = Field(int, 0)
    dichtekennwert = Field(int, 0)

    class Meta:
        workspace = 'definitions'


class Wohneinheiten(ProjectTable):

    id_teilflaeche = Field(int, 0)
    id_gebaeudetyp = Field(int, 0)
    name_gebaeudetyp = Field(str, 0)
    we = Field(int, 0)
    ew_je_we = Field(float, 0)
    korrekturfaktor = Field(float, 0)

    class Meta:
        workspace = 'definitions'
