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


class Markets(ProjectTable):

    name = Field(str, '')
    AGS = Field(str, '')
    adresse = Field(str, '')
    id_teilflaeche = Field(int, -1)
    id_betriebstyp_nullfall = Field(int, 0)
    betriebstyp_nullfall = Field(str, '')
    id_betriebstyp_planfall = Field(int, 0)
    betriebstyp_planfall = Field(str, '')
    id_kette = Field(int, 0)
    kette = Field(str, '')
    umsatz_nullfall = Field(float, 0)
    umsatz_planfall = Field(float, 0)
    umsatz_differenz = Field(float, 0)
    is_buffer = Field(bool, False)
    is_osm = Field(bool, False)
    vkfl = Field(int, 0)
    vkfl_planfall = Field(int, 0)

    class Meta:
        workspace = 'marketcompetition'


class MarketCellRelations(ProjectTable):

    id_markt = Field(int, 0)
    id_siedlungszelle = Field(int, 0)
    distanz = Field(int, 0)
    kk_strom_nullfall = Field(float, 0)
    kk_strom_planfall = Field(float, 0)
    kk_bindung_nullfall = Field(float, 0)
    kk_bindung_planfall = Field(float, 0)
    in_auswahl = Field(bool, False)
    luftlinie = Field(int, 0)

    class Meta:
        workspace = 'marketcompetition'





