# -*- coding: utf-8 -*-
import os
import subprocess
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QAction, QMenu

from pctools.base import PCDockWidget
from pctools.domains import (BewohnerArbeit, ProjectDefinitions,
                             Verkehr, Erreichbarkeiten)


class ProjektCheckMainDockWidget(PCDockWidget):

    ui_file = 'ProjektCheck_dockwidget_base.ui'

    def setupUi(self):
        #self.ui.pandas_button.clicked.connect(self.install_pandas)

        self.domains = []
        self.setup_projects()
        self.setup_definitions()
        self.setup_domains()
        self.setup_menu()

    def setup_projects(self):
        '''
        fill project combobox with available projects
        load active project? (or later after setting up domains?)
        '''
        # ToDo: fill with real projects
        self.project_combo.addItem("Projekt Bli")
        self.project_combo.addItem("Projekt Bla")
        self.project_combo.addItem("Projekt Blubb")

    def setup_definitions(self):
        '''setup project definitions widget'''
        self.project_definitions = ProjectDefinitions(iface=self.iface)
        self.definition_button.clicked.connect(self.project_definitions.show)

    def setup_domains(self):
        '''setup the domain widgets'''
        bewohner_arbeit = BewohnerArbeit(iface=self.iface)
        self.domains.append(bewohner_arbeit)

        erreichbarkeiten = Erreichbarkeiten(iface=self.iface)
        self.domains.append(erreichbarkeiten)

        verkehr = Verkehr(iface=self.iface)
        self.domains.append(verkehr)

    def setup_menu(self):
        '''fill the analysis menu with available domains'''
        menu = QMenu()
        for domain in self.domains:
            action = menu.addAction(domain.label)
            action.triggered.connect(domain.show)
        self.domain_button.setMenu(menu)

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

    def close(self):
        self.project_definitions.close()
        for domain in self.domains:
            domain.close()
        super().close()

    def unload(self):
        self.close()
        self.project_definitions.unload()
        del self.project_definitions
        for domain in self.domains:
            domain.unload()
            del domain
        super().unload()
