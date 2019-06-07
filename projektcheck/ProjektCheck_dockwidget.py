# -*- coding: utf-8 -*-
import os
import subprocess
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QAction, QMenu

from pctools.base import PCDockWidget
from pctools.domains import (BewohnerArbeit, ProjectDefinitions,
                             Verkehr, Erreichbarkeiten, Ecology,
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
        self.setup_projects()
        self.change_project(self.project_manager.active_project)

    def setup_projects(self):
        '''
        fill project combobox with available projects
        load active project? (or later after setting up domains?)
        '''
        for project in self.project_manager.projects:
            self.ui.project_combo.addItem(project.name, project)
        active_project = self.project_manager.active_project
        if active_project:
            index = self.ui.project_combo.findText(active_project.name)
            self.ui.project_combo.setCurrentIndex(index)
        self.ui.project_combo.currentIndexChanged.connect(
            lambda index: self.change_project(
                self.ui.project_combo.itemData(index))
        )

    def setup_definitions(self):
        '''setup project definitions widget'''
        self.project_definitions = ProjectDefinitions(iface=self.iface)
        self.ui.definition_button.clicked.connect(
            lambda: self.show_dockwidget(self.project_definitions))

    def setup_domains(self):
        '''setup the domain widgets'''
        # ToDo: load domains on demand only
        bewohner_arbeit = BewohnerArbeit(iface=self.iface)
        self.domains.append(bewohner_arbeit)

        erreichbarkeiten = Erreichbarkeiten(iface=self.iface)
        self.domains.append(erreichbarkeiten)

        verkehr = Verkehr(iface=self.iface)
        self.domains.append(verkehr)

        ecology = Ecology(iface=self.iface)
        self.domains.append(ecology)

        landuse = LandUse(iface=self.iface)
        self.domains.append(landuse)

        infrastructuralcosts = InfrastructuralCosts(iface=self.iface)
        self.domains.append(infrastructuralcosts)

        municipaltaxrevenue = MunicipalTaxRevenue(iface=self.iface)
        self.domains.append(municipaltaxrevenue)

        supermarkets = SupermarketsCompetition(iface=self.iface)
        self.domains.append(supermarkets)

    def setup_menu(self):
        '''fill the analysis menu with available domains'''
        # ToDo: remove old menu?
        menu = QMenu()
        for domain in self.domains:
            action = menu.addAction(domain.ui_label)
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
        active_project = self.project_manager.active_project
        if active_project:
            active_project.close()
        if self.project_definitions:
            self.project_definitions.unload()
            del self.project_definitions
        for domain in self.domains:
            domain.unload()
            del domain

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
        self.setup_menu()

        # ToDo: show last active widget

    def close(self):
        if self.project_definitions:
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
