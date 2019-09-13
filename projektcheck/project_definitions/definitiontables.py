from projektcheck.base import ProjectTable, Field, settings


class Framework(ProjectTable):
    ags = Field(int, 0)
    gemeinde_name = Field(str, '')
    gemeinde_typ = Field(int, 0)
    projekt_name = Field(str, '')

    class Meta:
        workspace = 'definitions'


class Areas(ProjectTable):

    nutzungsart = Field(int, 0)
    name = Field(str, '')
    aufsiedlungsdauer = Field(int, 0)
    validiert = Field(int, 0)
    beginn_nutzung = Field(int, 0)
    ags_bkg = Field(str, '')
    gemeinde_name = Field(str, '')
    we_gesamt = Field(int, 0)
    ap_gesamt = Field(int, 0)
    vf_gesamt = Field(int, 0)
    ew = Field(int, 0)
    wege_gesamt = Field(int, 0)
    wege_miv = Field(int, 0)

    class Meta:
        workspace = 'definitions'

    @classmethod
    def extra(cls):

        building_types = settings.BASEDATA.get_table(
            'Wohnen_Gebaeudetypen', 'Definition_Projekt'
        )
        assortments = settings.BASEDATA.get_table(
            'Einzelhandel_Sortimente', 'Definition_Projekt'
        )
        industries = settings.BASEDATA.get_table(
            'Gewerbe_Branchen', 'Definition_Projekt'
        )

        for bt in building_types.features():
            setattr(cls, bt.param_we, Field(int, default=0))
            setattr(cls, bt.param_ew_je_we,
                    Field(float, default=bt.default_ew_je_we))
        for branche in industries.features():
            setattr(cls, branche.param_gewerbenutzung, Field(int, default=16))
        for assortment in assortments.features():
            setattr(cls, assortment.param_vfl, Field(int, default=0))
