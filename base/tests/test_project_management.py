
# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'

import unittest
import shutil

from projektcheck.base.project import (ProjectManager, ProjectTable)
from projektcheck.base.geopackage import Geopackage
from projektcheck.base.database import Field
from projektcheck.settings import settings
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

    @classmethod
    def extra(cls):
        setattr(cls, 'extra_field', Field(int, default=-1))


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
        features = TestProjectTable.features(create=True)
        self.workspace = features.table.workspace
        assert len(features) == 0
        geom = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1), QgsPointXY(2, 2),
                                           QgsPointXY(2, 1)]])
        feat1 = features.add(name='first', geom=geom)
        assert feat1.extra_field == -1
        assert feat1.value == 1
        assert not feat1.is_true
        feat1.is_true = True
        feat1.name = 'new_name'
        feat1.save()
        feature = features.get(id=feat1.id)
        feature.name == 'new_name'
        assert isinstance(feature.geom, QgsGeometry)
        feat2 = features.add(name='second', geom=None, is_true=True)
        assert len(features) == 2
        for feature in features:
            assert feature.is_true
        feat2.delete()
        assert len(features) == 1
        features.delete(id=feat1.id)
        assert len(features) == 0


    def test_missing_fields(self):
        features = TestProjectTable.features(create=True)
        for i in range(5):
            features.add(name=i)
        TestProjectTable.missing = Field(int, default=50)
        features = TestProjectTable.features(create=True)
        df = features.to_pandas()
        assert df['missing'].unique()[0] == 50

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
