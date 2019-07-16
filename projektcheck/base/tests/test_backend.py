# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest
import random
import os

from projektcheck.base import Geopackage


class GeopackageTest(unittest.TestCase):
    """Test geopackage backend"""

    @classmethod
    def setUpClass(cls):
        cls.backend = Geopackage()
        #workspaces = self.backend.workspaces
        #self.workspace = self.backend.get_workspace(workspaces[0])
        cls.workspace = cls.backend.create_workspace('test', overwrite=True)

    def setUp(self):
        fields = {
            'id': int,
            'name': str,
            'value': float
        }
        self.table = self.workspace.create_table(
            'testtable', fields, geometry_type='Polygon', overwrite=True)
        self.table.add({
            'id': 1,
            'name': 'row1',
            'value': 5
        })
        self.table.add({
            'id': 2,
            'name': 'row2',
            'value': 5
        })
        self.table.add({
            'id': 3,
            'name': 'row3',
            'value': 6
        })
        self.table.add({
            'id': 3,
            'name': 'row4',
            'value': 0
        })
        #self.table.

    def tearDown(self):
        pass

    def test_filter(self):
        assert self.table.count == 4
        self.table.filter(value=6)
        assert self.table.count == 1
        self.table.filter(value=5)
        assert self.table.count == 2
        self.table.filter(value__in=[5, 6])
        assert self.table.count == 3
        self.table.filter(value__lt=4)
        assert self.table.count == 1
        self.table.filter(value__gt=7)
        assert self.table.count == 0

    def test_cursor(self):
        for i, row in enumerate(self.table):
            row['value'] = i
            self.table.update_cursor(row)
        self.table.filter(value=i)
        assert self.table.count == 1
        self.table.filter()
        assert self.table.count == 4

    def test_add_delete(self):
        assert self.table.count == 4
        new_row = {'value': 7}
        self.table.add(new_row)
        new_row = {'value': 5}
        self.table.add(new_row)
        assert self.table.count == 6
        n = self.table.delete(value=5)
        assert self.table.count == 3

    def test_pandas(self):
        a = self.table.as_pandas()

    @classmethod
    def tearDownClass(cls):
        cls.workspace.close()
        os.remove('test.gpkg')

if __name__ == "__main__":
    suite = unittest.makeSuite(GeopackageTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
