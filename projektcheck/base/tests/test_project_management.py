
# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest
import shutil

from projektcheck.base import (ProjectManager, ProjectTable, Field, Geopackage)
from settings import settings
from qgis.core import QgsGeometry, QgsPointXY

settings._write_instantly = False


class TestProjectTable(ProjectTable):
    name = Field(str)
    value = Field(float, default=1.0)
    is_true = Field(bool, default=False)

    class Meta:
        workspace = 'test'
        name = 'huhu'
        database = Geopackage
        geom = 'Polygon'


class ProjectTest(unittest.TestCase):
    """Test projects"""
    projectname = '__test__'

    @classmethod
    def setUpClass(cls):
        cls.project_manager = ProjectManager()
        if cls.projectname in [p.name for p in cls.project_manager.projects]:
            cls.project_manager.remove_project(cls.projectname)
        cls.project = cls.project_manager.create_project(cls.projectname)
        cls.project_manager.active_project = cls.project
        cls.workspace = None

    def test_project_table(self):
        table = TestProjectTable.get_table()
        self.workspace = table.workspace

    def test_features(self):
        features = TestProjectTable.features()
        self.workspace = features._table.workspace
        assert len(features) == 0
        geom = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2),
                                           QgsPointXY(2, 1)]])
        feature = features.add(name='first', geom=geom)
        assert feature.value == 1
        assert not feature.is_true
        feature = features.add(name='second', geom=None)
        assert len(features) == 2
        for feature in features:
            pass

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


if __name__ == "__main__":
    suite = unittest.makeSuite(ProjectTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
