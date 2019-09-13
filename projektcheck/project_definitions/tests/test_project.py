
# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest
import os
import time
from qgis.core import QgsVectorLayer, QgsApplication

from projektcheck.base import ProjectManager
from settings import settings
from projektcheck.project_definitions.project import init_project

#from qgis.core import QgsGeometry, QgsPointXY

settings._write_instantly = False


class ProjectTest(unittest.TestCase):
    """Test projects"""
    projectname = '__test__'

    @classmethod
    def setUpClass(cls):
        QgsApplication.setPrefixPath(
            "C:\Program Files\QGIS 3.6\bin\qgis-bin-g7.exe", True)
        qgs = QgsApplication([], True)
        qgs.initQgis()

        cls.project_manager = ProjectManager()
        if cls.projectname in [p.name for p in cls.project_manager.projects]:
            cls.project_manager.remove_project(cls.projectname)
        cls.project = cls.project_manager.create_project(cls.projectname)
        cls.project_manager.active_project = cls.project
        cls.workspace = None

    def test_project_creation(self):
        shape_path = os.path.join(
            self.project_manager.settings.TEMPLATE_PATH,
            'projektflaechen', 'projektflaechen_template.shp')
        layer = QgsVectorLayer(shape_path, 'testlayer_shp', 'ogr')
        init_project(self.project, layer, self.project_manager.settings.EPSG)

    def tearDown(self):
        if self.workspace:
            self.workspace.close()

    @classmethod
    def tearDownClass(cls):
        #project = ProjectManager().active_project
        #database = Geopackage(project.path, read_only=False)
        #database.remove_workspace('test')
        #cls.project.close()
        if cls.workspace:
            cls.workspace.close()
        cls.project_manager.remove_project(cls.project)
        qgs.exitQgis()


if __name__ == "__main__":
    suite = unittest.makeSuite(ProjectTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

