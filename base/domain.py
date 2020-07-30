# -*- coding: utf-8 -*-
'''
***************************************************************************
    domain.py
    ---------------------
    Date                 : July 2019
    Copyright            : (C) 2019 by Christoph Franke
    Email                : franke at ggr-planung dot de
***************************************************************************
*                                                                         *
*   This program is free software: you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

widgets representing different "areas of knowledge"
'''

__author__ = 'Christoph Franke'
__date__ = '16/07/2019'

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt, QObject, QThread
from qgis import utils
from qgis.gui import QgisInterface, QgsMapCanvas
import os

from .project import (ProjectManager, ProjectLayer,
                      Project, Settings)
from .database import Database
from projektcheck.settings import settings


class PCDockWidget(QObject):
    '''
    dock widget, can be rendered in QGIS

    Attributes
    ----------
    ui : QDockWidget
        the actual qwidget holding all child ui elements
    ui_file : str
        the qt ui file used for rendering the widget
    value : basic_type
        current value of the parameter
    closingWidget : pyqtSignal
        fired when widget is closed
    project : Project
        active project
    settings : Settings
        projekt-check related settings
    projectdata : Database,
        database of the active project
    basedata : Database,
        database with all base data
    project_manager : ProjectManager
        ProjectManager instance
    '''
    ui_file = None
    closing_widget = pyqtSignal()
    project_manager = ProjectManager()

    def __init__(self, iface: QgisInterface = None, canvas: QgsMapCanvas = None,
                 position: int = Qt.RightDockWidgetArea):
        '''
        Parameters
        ----------
        iface : QgisInterface, optional
            instance of QGIS interface, defaults to the interface of the QGIS
            instance in use
        canvas : QgsMapCanvas, optional
            the map canvas, defaults to the canvas of the interface
        position : int, optional
            dock widget area to add the dock widget to, defaults to attach the
            widget in the right section of QGIS (Qt.RightDockWidgetArea)
        '''
        super().__init__()
        self.iface = iface or utils.iface
        self.canvas = canvas or self.iface.mapCanvas()
        self.initial_position = position
        self.ui = QtWidgets.QDockWidget()
        # look for file ui folder if not found
        ui_file = self.ui_file if os.path.exists(self.ui_file) \
            else os.path.join(settings.UI_PATH, self.ui_file)
        uic.loadUi(ui_file, self.ui)
        #self.ui.setAllowedAreas(
            #Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea |
            #Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea
        #)
        self.ui.closeEvent = self.closeEvent
        self.is_active = False
        self.setupUi()

    def setupUi(self):
        '''
        setup ui, called when widget is initially set up
        override in sub classes to setup the ui elements of the widget
        '''
        pass

    def load_content(self):
        '''
        load ui content, called when widget is shown
        '''
        pass

    def close(self):
        '''
        override, set inactive on close
        '''
        self.is_active = False
        try:
            self.ui.close()
        # ui might already be deleted by QGIS
        except RuntimeError:
            pass

    def show(self):
        '''
        show the widget inside QGIS
        '''
        if self.is_active:
            self.ui.show()
            return
        self.load_content()
        self.iface.addDockWidget(self.initial_position, self.ui)
        self.is_active = True

    def unload(self):
        '''
        unload the widget
        '''
        self.is_active = False
        self.close()
        self.iface.removeDockWidget(self.ui)
        self.ui.deleteLater()

    def closeEvent(self, event):
        '''
        override, emits closing signal on close
        '''
        try:
            self.closing_widget.emit()
        except:
            pass
        event.accept()

    @property
    def project(self) -> Project:
        '''
        the project currently active
        '''
        return self.project_manager.active_project

    @property
    def settings(self) -> Settings:
        '''
        the settings of Projekt-Check
        '''
        return self.project_manager.settings

    @property
    def basedata(self) -> Database:
        '''
        the database with the base data of Projekt-Check
        '''
        return self.project_manager.basedata

    @property
    def projectdata(self) -> Database:
        '''
        the database with the base data of Projekt-Check
        '''
        if not self.project_manager.active_project:
            return
        return self.project_manager.active_project.data


class Domain(PCDockWidget):
    '''
    dock widget for specific area of ​​knowledge

    Attributes
    ----------
    label : str
        label for area of knowledge displayed in ui
    ui : QDockWidget
        the actual qwidget holding all child ui elements
    ui_file : str
        the qt ui file used for rendering the widget
    value : basic_type
        current value of the parameter
    closingWidget : pyqtSignal
        fired when widget is closed
    project : Project
        active project
    settings : Settings
        projekt-check related settings
    projectdata : Database,
        database of the active project
    basedata : Database,
        database with all base data
    '''
    ui_label = None
    ui_icon = ""
    layer_group = ''

    def __init__(self, iface: QgisInterface = None, canvas: QgsMapCanvas = None,
                 position: int = Qt.RightDockWidgetArea):
        '''
        Parameters
        ----------
        iface : QgisInterface, optional
            instance of QGIS interface, defaults to the interface of the QGIS
            instance in use
        canvas : QgsMapCanvas, optional
            the map canvas, defaults to the canvas of the interface
        position : int, optional
            dock widget area to add the dock widget to, defaults to attach the
            widget in the right section of QGIS (Qt.RightDockWidgetArea)
        '''
        super().__init__(iface=iface, canvas=canvas, position=position)
        self.ui.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)

    def load_content(self):
        '''
        Called when domain is opened by user. Shows domain group when opening
        domain. Extend to load input data for domain and set the content of to
        the UI elements
        '''
        # some domains open the project definition and it is opened after
        # loading a project, close it by default
        def_group = ProjectLayer.find_group('Projektdefinition')
        if def_group:
            def_group.setItemVisibilityChecked(False)
        if self.layer_group:
            group = ProjectLayer.find_group(self.layer_group)
            if group:
                group.setItemVisibilityChecked(True)
                group.parent().setItemVisibilityChecked(True)

    def close(self):
        '''
        override, hide domain group on close
        '''
        super().close()
        if self.layer_group:
            group = ProjectLayer.find_group(self.layer_group)
            if group:
                group.setItemVisibilityChecked(False)
                parent = group.parent()
                # in case parent is sub-group of project group, hide as well
                if parent.name() != self.project.groupname:
                    parent.setItemVisibilityChecked(False)


class Worker(QThread):
    '''
    abstract worker

    Attributes
    ----------
    finished : pyqtSignal
        emitted when all tasks are finished, success True/False
    error : pyqtSignal
        emitted on error while working, error message text
    message : pyqtSignal
        emitted when a message is send, message text
    progress : pyqtSignal
        emitted on progress, progress in percent
    '''

    # available signals to be used in the concrete worker
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    message = pyqtSignal(str)
    progress = pyqtSignal(float)

    def __init__(self, parent: QObject = None):
        '''
        Parameters
        ----------
        parent : QObject, optional
            parent object of thread, defaults to no parent (global)
        '''
        #parent = parent or utils.iface.mainWindow()
        super().__init__(parent=parent)

    def run(self, on_success: object = None):
        '''
        runs code defined in self.work
        emits self.finished on success and self.error on exception
        override this function if you make asynchronous calls

        Parameters
        ----------
        on_success : function
            function to execute on success
        '''
        try:
            result = self.work()
            self.finished.emit(result)
            if on_success:
                on_success()
        except Exception as e:
            self.error.emit(str(e))

    def work(self) -> object:
        '''
        override
        code to be executed when running worker

        Returns
        -------
        result : object
            result of work, emitted when code was run succesfully
        '''
        raise NotImplementedError

    def log(self, message):
        '''
        emits message

        Parameters
        ----------
        message : str
        '''
        self.message.emit(str(message))

    def set_progress(self, progress: int):
        '''
        emits progress

        Parameters
        ----------
        progress : int
            progress in percent, value in range [0, 100]
        '''
        self.progress.emit(progress)


