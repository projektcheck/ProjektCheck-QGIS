
# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'

import unittest
import os
from utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()
from processing.core.Processing import Processing
Processing.initialize()

from qgis.core import QgsVectorLayer

from projektcheck.settings import settings
from projektcheck.base.project import ProjectManager
from projektcheck.base.geopackage import Geopackage
from projektcheck.domains.definitions.project import ProjectInitialization

settings._write_instantly = False


class ProjectTest(unittest.TestCase):
    """Test projects"""
    projectname = '__test__'

    @classmethod
    def setUpClass(cls):
        cls.project_manager = ProjectManager()
        cls.project_manager.basedata = Geopackage(base_path='.', read_only=True)
        if cls.projectname in [p.name for p in cls.project_manager.projects]:
            cls.project_manager.remove_project(cls.projectname)
        cls.workspace = None

    def test_project_creation(self):
        shape_path = os.path.join(
            self.project_manager.settings.TEMPLATE_PATH,
            'projektflaechen', 'projektflaechen_template.shp')
        layer = QgsVectorLayer(shape_path, 'testlayer_shp', 'ogr')
        job = ProjectInitialization(self.projectname, layer,
                                    self.project_manager.settings.EPSG)
        self.project = job.work()

    @classmethod
    def tearDownClass(cls):
        cls.project_manager.remove_project(cls.projectname)


if __name__ == "__main__":
    suite = unittest.makeSuite(ProjectTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

