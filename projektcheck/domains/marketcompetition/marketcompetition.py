from projektcheck.base.domain import Domain
from projektcheck.utils.utils import add_selection_icons


class SupermarketsCompetition(Domain):
    """"""

    ui_label = 'Standortkonkurrenz und Supermärkte'
    ui_file = 'ProjektCheck_dockwidget_analysis_08-SKSM.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_supermarkets_1.png"

    def setupUi(self):
        add_selection_icons(self.ui.toolBox)
