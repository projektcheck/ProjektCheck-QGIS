# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest
import random
import os

from pctools.base import Geopackage


class GeopackageTest(unittest.TestCase):
    """Test geopackage backend"""

    @classmethod
    def setUpClass(cls):
        cls.backend = Geopackage()
        #workspaces = self.backend.workspaces
        #self.workspace = self.backend.get_workspace(workspaces[0])
        cls.workspace = cls.backend.create_workspace('test', overwrite=True)
        fields = {
            'id': int,
            'name': str,
            'value': float
        }
        cls.table = cls.workspace.create_table('testtable', fields,
                                                 geometry_type='Polygon')
        print(cls.table.fields)
        cls.table.add({
            'id': 1,
            'name': 'row1'
        })
        cls.table.add({
            'id': 2,
            'name': 'row2'
        })
        #self.table.

    def tearDown(self):
        pass

    def test_cursor(self):
        for i, row in enumerate(self.table):
            row['value'] = i
            self.table.update_cursor(row)
        self.table.where = f'"value" = {i}'
        assert self.table.count == 1
        self.table.where = ''
        assert self.table.count == 2

    def test_add_delete(self):
        assert self.table.count == 2
        new_row = {'id': 3}
        self.table.add(new_row)
        assert self.table.count == 3
        n = self.table.delete('"id" = 3')
        assert self.table.count == 2

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
