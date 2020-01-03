# -*- coding: utf-8 -*-
import os
import subprocess
from qgis.PyQt.QtWidgets import QMenu, QInputDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import  QgsProject

from projektcheck.base.domain import PCDockWidget
from projektcheck.base.dialogs import (SettingsDialog, NewProjectDialog,
                                       ProgressDialog)
from projektcheck.base.project import (ProjectLayer, OSMBackgroundLayer,
                                       TerrestrisBackgroundLayer)
from projektcheck.base.database import Workspace
from projektcheck.domains.definitions.tables import Teilflaechen
from projektcheck.domains.definitions.project import (ProjectInitialization,
                                                      CloneProject)
from projektcheck.domains import (JobsInhabitants, ProjectDefinitions,
                                  Traffic, Reachabilities, Ecology,
                                  LandUse, InfrastructuralCosts,
                                  MunicipalTaxRevenue,
                                  SupermarketsCompetition)


class ProjektCheckMainDockWidget(PCDockWidget):

    ui_file = 'ProjektCheck_dockwidget_base.ui'

    def setupUi(self):
        #self.ui.pandas_button.clicked.connect(self.install_pandas)
        self.domains = []
        self.active_dockwidget = None
        self.project_definitions = None

        settings_dialog = SettingsDialog(self.settings.project_path)
        def set_project_path(path):
            if not path:
                return
            self.settings.project_path = path
            self.setup_projects()
        self.ui.settings_button.clicked.connect(
            lambda: set_project_path(settings_dialog.show()))

        def create_project():
            dialog = NewProjectDialog()
            ok, name, layer = dialog.show()

            if ok:
                job = ProjectInitialization(name, layer,
                                            self.project_manager.settings.EPSG,
                                            parent=self.ui)
                def on_success(project):
                    self.ui.project_combo.addItem(project.name, project)
                    self.ui.project_combo.setCurrentIndex(
                        self.ui.project_combo.count() - 1)
                    self.project_manager.active_project = project

                dialog = ProgressDialog(job, parent=self.ui,
                                        on_success=on_success)
                dialog.show()

        self.ui.create_project_button.clicked.connect(create_project)

        def remove_project():
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
                self.project_manager.active_project = ''
                for ws in Workspace.get_instances():
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
                self.project_manager.remove_project(project)
                self.canvas.refreshAllLayers()
        self.ui.remove_project_button.clicked.connect(remove_project)

        def clone_project():
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

        self.ui.clone_project_button.clicked.connect(clone_project)


        self.setup_projects()

    def setup_projects(self):
        '''
        fill project combobox with available projects
        load active project? (or later after setting up domains?)
        '''
        self.ui.project_combo.model().item(0).setEnabled(False)
        self.ui.domain_button.setEnabled(False)
        self.ui.definition_button.setEnabled(False)
        for project in self.project_manager.projects:
            if project.name == '__test__':
                continue
            self.ui.project_combo.addItem(project.name, project)
        self.ui.project_combo.currentIndexChanged.connect(
            lambda index: self.change_project(
                self.ui.project_combo.itemData(index))
        )
        #active_project = self.project_manager.active_project
        #if active_project:
            #index = self.ui.project_combo.findText(active_project.name)
            #self.ui.project_combo.setCurrentIndex(index)
        # load active project
        #self.change_project(self.project_manager.active_project)

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

        municipaltaxrevenue = MunicipalTaxRevenue()
        self.domains.append(municipaltaxrevenue)

        supermarkets = SupermarketsCompetition()
        self.domains.append(supermarkets)

        # fill the analysis menu with available domains
        menu = QMenu()
        for domain in self.domains:
            current_dir = os.path.dirname(os.path.realpath(__file__))
            icon = QIcon(os.path.join(current_dir, domain.ui_icon))
            action = menu.addAction(icon, domain.ui_label)
            action.triggered.connect(
                lambda e, d=domain: self.show_dockwidget(d))
        self.ui.domain_button.setMenu(menu)

    def install_pandas(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        process = subprocess.Popen(os.path.join(dir_path, 'install-pandas.bat'),
                                   shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        #process = subprocess.Popen(['runas', '/user:Administrator', '/noprofile', os.path.join(dir_path, 'install-pandas.bat')], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,stdin=subprocess.PIPE)#os.path.join(dir_path, 'install-pandas.bat')])
        #process.stdin.write(b'')
        stdout, stderr = process.communicate()
        print('STDOUT:{}'.format(stdout))
        print('STDERR:{}'.format(stderr))

    def show_dockwidget(self, widget):
        if self.active_dockwidget:
            self.active_dockwidget.close()
        self.active_dockwidget = widget
        widget.show()

    def change_project(self, project):
        try:
            active_project = self.project_manager.active_project
            #if active_project:
                #active_project.close()
            if getattr(self, 'project_definitions', None):
                self.project_definitions.unload()
                del self.project_definitions
            for domain in self.domains:
                domain.unload()
                del domain
            # ToDo: put that in project.close() and get
            # workspaces of this project only
            for ws in Workspace.get_instances():
                if not ws.database.read_only:
                    ws.close()

            if not project:
                self.ui.domain_button.setEnabled(False)
                self.ui.definition_button.setEnabled(False)
                return
            else:
                self.ui.domain_button.setEnabled(True)
                self.ui.definition_button.setEnabled(True)

            self.project_manager.active_project = project

            self.setup_definitions()
            self.setup_domains()

            table = Teilflaechen.get_table()
            layer_root = QgsProject.instance().layerTreeRoot()
            for child in layer_root.children():
                name = child.name()
                if name.startswith('Projekt'):
                    child.setItemVisibilityChecked(name==project.groupname)

            output = ProjectLayer.from_table(
                table, groupname='Projektdefinition')
            output.draw(label='Nutzungen des Plangebiets',
                        style_file='definitions.qml')
            output = ProjectLayer.from_table(table, groupname='Hintergrund',
                                             prepend=False)
            output.draw(label='Umriss des Plangebiets', style_file='areas.qml')

            backgroundOSM = OSMBackgroundLayer(groupname='Hintergrundkarten')
            backgroundOSM.draw(checked=False)
            backgroundGrey = TerrestrisBackgroundLayer(
                groupname='Hintergrundkarten')
            backgroundGrey.draw()

            output.zoom_to()
            # ToDo: show last active widget
        # ToDo: specific exceptions
        except Exception as e:
            message = QMessageBox()
            message.setIcon(QMessageBox.Warning)
            message.setText(f'Das Projekt "{project.name}" ist beschädigt.')
            message.setInformativeText('Bitte löschen Sie das Projekt oder '
                                       'wenden Sie sich an den Administrator')
            message.setWindowTitle('Fehler')
            message.setDetailedText(str(e))
            message.exec_()

    def close(self):
        if getattr(self, 'project_definitions', None):
            self.project_definitions.close()
        for domain in self.domains:
            domain.close()
        super().close()

    def unload(self):
        self.close()
        if self.project_definitions:
            self.project_definitions.unload()
            del self.project_definitions
        for domain in self.domains:
            domain.unload()
            del domain
        super().unload()
