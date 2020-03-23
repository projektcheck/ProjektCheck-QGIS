# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QMenu, QInputDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject

from projektchecktools.base.domain import PCDockWidget
from projektchecktools.base.dialogs import (SettingsDialog, NewProjectDialog,
                                            ProgressDialog)
from projektchecktools.base.project import (ProjectLayer, OSMBackgroundLayer,
                                            TerrestrisBackgroundLayer)
from projektchecktools.base.database import Workspace
from projektchecktools.domains.definitions.project import (
    ProjectInitialization, CloneProject)
from projektchecktools.utils.utils import open_file
from projektchecktools.domains import (JobsInhabitants, ProjectDefinitions,
                                       Traffic, Reachabilities, Ecology,
                                       LandUse, InfrastructuralCosts,
                                       MunicipalTaxRevenue,
                                       SupermarketsCompetition)
from projektchecktools.domains.definitions.tables import Projektrahmendaten


class ProjektCheckMainDockWidget(PCDockWidget):

    ui_file = 'ProjektCheck_dockwidget_base.ui'

    def setupUi(self):
        #self.ui.pandas_button.clicked.connect(self.install_pandas)
        self.domains = []
        self.active_dockwidget = None
        self.project_definitions = None

        self.ui.settings_button.clicked.connect(self.show_settings)

        self.ui.create_project_button.clicked.connect(self.create_project)
        self.ui.remove_project_button.clicked.connect(self.remove_project)
        self.ui.clone_project_button.clicked.connect(self.clone_project)

        self.setup_help()

        self.ui.project_combo.currentIndexChanged.connect(
            lambda index: self.change_project(
                self.ui.project_combo.itemData(index)))

        self.setup_projects()

    def show(self):
        super().show()
        valid, msg = self.project_manager.check_basedata()
        if valid == -1:
            QMessageBox.warning(self.ui, 'Warnung', msg)

        # base data not up to date
        elif valid != 2:
            reply = QMessageBox.question(
                self.ui, 'Basisdaten aktualisieren',
                f'{msg}\n\n'
                'Möchten Sie die Basisdaten jetzt herunterladen? '
                '(Alternativ können Sie sie auch in den Projekt-'
                'Check-Einstellungen herunterladen.)',
                 QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                settings = SettingsDialog(self)
                settings.download_basedata()

    def show_settings(self):
        settings_dialog = SettingsDialog(self)
        prev_path = self.settings.project_path
        confirmed = settings_dialog.exec()
        if confirmed:
            self.project_manager.load_basedata()
            if prev_path != self.settings.project_path:
                if self.active_dockwidget:
                    self.active_dockwidget.close()
                self.setup_projects()

    def create_project(self):
        status, msg = self.project_manager.check_basedata()
        if status == 0:
            QMessageBox.warning(self.ui, 'Hinweis', msg)
            self.ui.project_combo.setCurrentIndex(0)
            return
        dialog = NewProjectDialog()
        ok, name, layer = dialog.show()

        if ok:
            job = ProjectInitialization(name, layer,
                                        self.project_manager.settings.EPSG,
                                        parent=self.ui)
            def on_success(project):
                self.project_manager.active_project = project
                self.ui.project_combo.addItem(project.name, project)
                self.ui.project_combo.setCurrentIndex(
                    self.ui.project_combo.count() - 1)

            dialog = ProgressDialog(job, parent=self.ui,
                                    on_success=on_success)
            dialog.show()

    def clone_project(self):
        project = self.project_manager.active_project
        if not project:
            return
        name = f'{project.name}_kopie'
        existing_names = [p.name for p in self.project_manager.projects]
        while True:
            name, ok = QInputDialog.getText(
                self.ui, f'{project.name} kopieren',
                'Name des neuen Projekts', text=name)
            if ok:
                if name in existing_names:
                    QMessageBox.warning(
                        self.ui, 'Hinweis',
                        'Ein Projekt mit diesem Namen ist '
                        'bereits vorhanden')
                    continue

                job = CloneProject(name, project, parent=self.ui)
                def on_success(project):
                    self.ui.project_combo.addItem(project.name, project)
                    self.ui.project_combo.setCurrentIndex(
                        self.ui.project_combo.count() - 1)
                    self.project_manager.active_project = project

                dialog = ProgressDialog(job, parent=self.ui,
                                        on_success=on_success)
                dialog.show()
            break

    def remove_project(self):
        project = self.project_manager.active_project
        if not project:
            return
        reply = QMessageBox.question(
            self.ui, 'Projekt entfernen',
            f'Soll das Projekt "{project.name}" entfernt werden?\n'
            '(alle Projektdaten werden gelöscht)',
             QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            idx = self.ui.project_combo.currentIndex()
            if self.active_dockwidget:
                self.active_dockwidget.close()
            self.ui.project_combo.setCurrentIndex(0)
            self.ui.project_combo.removeItem(idx)
            instances = list(Workspace.get_instances())
            for ws in instances:
                # close all writable workspaces (read_only indicate the
                # base data)
                # ToDo: adress project workspaces somehow else
                if not ws.database.read_only:
                    ws.close()
            # close and remove layers in project group (in TOC)
            qgisproject = QgsProject.instance()
            root = qgisproject.layerTreeRoot()
            project_group = root.findGroup(project.groupname)
            if project_group:
                for layer in project_group.findLayers():
                    qgisproject.removeMapLayer(layer.layerId())
                project_group.removeAllChildren()
                root.removeChildNode(project_group)
            # wait for canvas to refresh because it blocks the datasources for
            # the layers as long they are visible
            def on_refresh():
                self.project_manager.remove_project(project)
                self.project_manager.active_project = None
                self.canvas.mapCanvasRefreshed.disconnect(on_refresh)
            self.canvas.mapCanvasRefreshed.connect(on_refresh)
            self.canvas.refreshAllLayers()

    def setup_projects(self):
        '''
        fill project combobox with available projects
        load active project? (or later after setting up domains?)
        '''
        self.ui.project_combo.blockSignals(True)
        self.ui.project_combo.clear()
        self.ui.project_combo.addItem('Projekt wählen')
        self.ui.project_combo.model().item(0).setEnabled(False)
        self.ui.domain_button.setEnabled(False)
        self.ui.definition_button.setEnabled(False)
        self.project_manager.reset_projects()
        for project in self.project_manager.projects:
            if project.name == '__test__':
                continue
            self.ui.project_combo.addItem(project.name, project)
        self.ui.project_combo.blockSignals(False)

    def setup_definitions(self):
        '''setup project definitions widget'''
        self.project_definitions = ProjectDefinitions()
        #self.project_definitions.reset()
        self.ui.definition_button.clicked.connect(
            lambda: self.show_dockwidget(self.project_definitions))

    def setup_domains(self):
        '''setup the domain widgets'''

        self.domains = []

        bewohner_arbeit = JobsInhabitants()
        self.domains.append(bewohner_arbeit)

        erreichbarkeiten = Reachabilities()
        self.domains.append(erreichbarkeiten)

        verkehr = Traffic()
        self.domains.append(verkehr)

        ecology = Ecology()
        self.domains.append(ecology)

        landuse = LandUse()
        self.domains.append(landuse)

        infrastructuralcosts = InfrastructuralCosts()
        self.domains.append(infrastructuralcosts)

        inactive = []

        municipaltaxrevenue = MunicipalTaxRevenue()
        inactive.append(municipaltaxrevenue)

        supermarkets = SupermarketsCompetition()
        inactive.append(supermarkets)

        # fill the analysis menu with available domains
        menu = QMenu()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        for domain in self.domains:
            icon = QIcon(os.path.join(current_dir, domain.ui_icon))
            action = menu.addAction(icon, domain.ui_label)
            action.triggered.connect(
                lambda e, d=domain: self.show_dockwidget(d))

        for domain in inactive:
            icon = QIcon(os.path.join(current_dir, domain.ui_icon))
            action = menu.addAction(icon, f'{domain.ui_label} (demnächst)')
            action.setEnabled(False)

        self.ui.domain_button.setMenu(menu)

    def setup_help(self):
        menu = QMenu()
        help_path = self.settings.HELP_PATH
        current_dir = os.path.dirname(os.path.realpath(__file__))

        # Overview
        icon_path = 'images/iconset_mob/20190619_iconset_mob_info_1.png'
        pdf_path = os.path.join(
            help_path, 'Anleitung_Gesamtueberblick.pdf')
        action = menu.addAction(
            QIcon(os.path.join(current_dir, icon_path)), 'Schnelleinstieg')
        action.triggered.connect(lambda b, p=pdf_path: open_file(p))

        # About
        icon_path = 'images/icon.png'
        pdf_path = os.path.join(
            help_path, 'About.pdf')
        action = menu.addAction(
            QIcon(os.path.join(current_dir, icon_path)), 'Über Projekt-Check')
        action.triggered.connect(lambda b, p=pdf_path: open_file(p))

        # Legal notes
        icon_path = 'images/iconset_mob/20190619_iconset_mob_legal_01.png'
        pdf_path = os.path.join(
            help_path, 'Haftungsausschluss.pdf')
        action = menu.addAction(
            QIcon(os.path.join(current_dir, icon_path)), 'Haftungssausschluss')
        action.triggered.connect(lambda b, p=pdf_path: open_file(p))

        self.ui.help_button.setMenu(menu)

    def show_dockwidget(self, widget):
        if self.active_dockwidget:
            self.active_dockwidget.close()
        else:
            tree_layer = ProjectLayer.find(ProjectDefinitions.layer_group)
            if tree_layer:
                tree_layer[0].setItemVisibilityChecked(False)
        self.active_dockwidget = widget
        widget.show()

    def change_project(self, project):
        if not project:
            self.ui.domain_button.setEnabled(False)
            self.ui.definition_button.setEnabled(False)
            return
        status, msg = self.project_manager.check_basedata()
        if status == 0:
            QMessageBox.warning(self.ui, 'Hinweis', msg)
            self.ui.project_combo.setCurrentIndex(0)
            return
        projektrahmendaten = Projektrahmendaten.features(project=project)[0]
        self.project_manager.load_basedata(
            version=projektrahmendaten.basisdaten_version)
        try:
            if getattr(self, 'project_definitions', None):
                self.project_definitions.unload()
                del(self.project_definitions)
            for domain in self.domains:
                domain.unload()
                del(domain)
            # ToDo: put that in project.close() and get
            # workspaces of this project only
            for ws in Workspace.get_instances():
                if not ws.database.read_only:
                    ws.close()

            self.project_manager.active_project = project

            self.setup_definitions()
            self.setup_domains()

            # append groups to force initial order of layers
            ProjectLayer.add_group(self.project_definitions.layer_group,
                                   prepend=True)
            for domain in self.domains:
                group = ProjectLayer.add_group(domain.layer_group,
                                               prepend=False)
                group.setItemVisibilityChecked(False)

            # check active project, uncheck other projects
            layer_root = QgsProject.instance().layerTreeRoot()
            for p in self.project_manager.projects:
                group = layer_root.findGroup(p.groupname)
                if group:
                    group.setItemVisibilityChecked(
                        p.groupname==project.groupname)

            # show area layers
            self.project_definitions.show_outputs(zoom=True)

            backgroundOSM = OSMBackgroundLayer(groupname='Hintergrundkarten')
            backgroundOSM.draw(checked=False)
            backgroundGrey = TerrestrisBackgroundLayer(
                groupname='Hintergrundkarten')
            backgroundGrey.draw()
            self.ui.domain_button.setEnabled(True)
            self.ui.definition_button.setEnabled(True)
            # ToDo: show last active widget
        except FileNotFoundError as e:
            message = QMessageBox()
            message.setIcon(QMessageBox.Warning)
            message.setText(f'Das Projekt "{project.name}" ist beschädigt.')
            message.setInformativeText('Bitte löschen Sie das Projekt oder '
                                       'wenden Sie sich an den Administrator')
            message.setWindowTitle('Fehler')
            message.setDetailedText(str(e))
            message.exec_()

    def close(self):
        self.close_all_projects()
        super().close()

    def close_all_projects(self):
        if getattr(self, 'project_definitions', None):
            self.project_definitions.close()
        if getattr(self, 'domains', None):
            for domain in self.domains:
                domain.close()
        qgisproject = QgsProject.instance()
        layer_root = qgisproject.layerTreeRoot()
        # remove all project layers from layer tree
        for project in self.project_manager.projects:
            group = layer_root.findGroup(project.groupname)
            if group:
                for layer in group.findLayers():
                    qgisproject.removeMapLayer(layer.layerId())
                group.removeAllChildren()
                layer_root.removeChildNode(group)
        for ws in Workspace.get_instances():
            if not ws.database.read_only:
                ws.close()
        self.canvas.refreshAllLayers()

    def unload(self):
        print('unloading Projekt-Check')
        self.close()
        if getattr(self, 'project_definitions', None):
            self.project_definitions.unload()
            del(self.project_definitions)
        if getattr(self, 'domains', None):
            for domain in self.domains:
                domain.unload()
                del(domain)
        super().unload()
