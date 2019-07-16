
# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest
import shutil

from projektcheck.base import (ProjectManager, ProjectTable, Field, Geopackage)
from settings import settings

settings._write_instantly = False


class TestProjectTable(ProjectTable):
    id = Field(int, default=0)
    name = Field(str)
    value = Field(float, default=1.0)
    is_true = Field(bool, default=False)

    class Meta:
        workspace = 'test'
        name = 'huhu'


class ProjectTest(unittest.TestCase):
    """Test projects"""
    projectname = '__test__'

    @classmethod
    def setUpClass(cls):
        cls.project_manager = ProjectManager()
        if cls.projectname in cls.project_manager.projects:
            cls.project_manager.remove_project(cls.projectname)
        cls.project = cls.project_manager.create_project(cls.projectname)
        cls.project_manager.active_project = cls.project

    @classmethod
    def tearDownClass(cls):
        cls.project_manager.remove_project(cls.project)

    def test_project_table(self):
        table = TestProjectTable.get()
        print(table)


if __name__ == "__main__":
    suite = unittest.makeSuite(ProjectTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
