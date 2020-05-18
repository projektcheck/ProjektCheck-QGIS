from qgis.PyQt.QtWidgets import QMessageBox

from projektchecktools.base.domain import Domain
from projektchecktools.domains.municipaltaxrevenue.tables import (
    Gemeinden, EinwohnerWanderung)
from projektchecktools.domains.municipaltaxrevenue.migration import (
    Migration)
from projektchecktools.domains.definitions.tables import (
    Projektrahmendaten, Teilflaechen)


class MunicipalTaxRevenue(Domain):
    """"""

    ui_label = 'kommunale Steuereinnahmen'
    ui_file = 'ProjektCheck_dockwidget_analysis_07-KSt.ui'
    ui_icon = "images/iconset_mob/20190619_iconset_mob_domain_tax_1.png"
    layer_group = 'Wirkungsbereich 7 - Kommunale Steuereinnahmen'
    radius = 25000

    def setupUi(self):
        self.ui.migration_inhabitants_button.clicked.connect(
            self.calculate_migration_inhabitants)

    def load_content(self):
        super().load_content()
        self.gemeinden = Gemeinden.features(create=True)
        self.project_frame = Projektrahmendaten.features()[0]
        self.wanderung_einw = EinwohnerWanderung.features(create=True)
        if len(self.gemeinden) == 0:
            self.get_gemeinden()

        self.areas = Teilflaechen.features()

    def get_gemeinden(self):
        gemeinden = self.basedata.get_table('bkg_gemeinden',
                                            'Basisdaten_deutschland')
        buffer_geom = self.project_frame.geom.buffer(self.radius, 5)
        gemeinden.spatial_filter(buffer_geom.asWkt())
        # project table has some of the fields of the basedata table
        # (same names)
        common_fields = set([f.name for f in gemeinden.fields()]).intersection(
            [f.name for f in self.gemeinden.fields()])
        for gemeinde in gemeinden:
            attrs = {}
            for field in common_fields:
                attrs[field] = gemeinde[field]
            attrs['geom'] = gemeinde['geom']
            self.gemeinden.add(**attrs)

    def calculate_migration_inhabitants(self):
        sum_ew = sum(self.areas.values('ew'))
        if sum_ew == 0:
            QMessageBox.warning(self.ui, 'Fehler',
                                'Es wurden keine definierten Teilflächen mit '
                                'der Nutzungsart "Wohnen" gefunden.')
            return

        job = Migration(self.project)

        def on_success(r):
            self.show_results()

        job.work()
        #dialog = ProgressDialog(job, parent=self.ui, on_success=on_success)
        #dialog.show()


    def setup_params(self):
        pass