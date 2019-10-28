from projektcheck.base.domain import Domain
from projektcheck.utils.utils import add_selection_icons


class Reachabilities(Domain):
    """"""

    ui_label = 'Erreichbarkeiten'
    ui_file = 'ProjektCheck_dockwidget_analysis_02-Err.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_get_time_stop2central_2.png"

    def setupUi(self):
        add_selection_icons(self.ui.toolBox)
