# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest
import random

from pctools.base import Geopackage


class GeopackageTest(unittest.TestCase):
    """Test geopackage backend"""

    def setUp(self):
        self.backend = Geopackage()
        workspaces = self.backend.workspaces
        self.workspace = self.backend.get_workspace(workspaces[0])
        tables = self.workspace.tables
        self.table = self.workspace.get_table('Projektrahmendaten')

    def tearDown(self):
        pass

    def test_cursor(self):
        new_val = random.randint(0, 50)
        for row in self.table:
            row['Gemeindetyp'] = new_val
            self.table.update_cursor(row)
        self.table.where = f'"Gemeindetyp" = {new_val}'
        assert self.table.count == 2

    def test_add_delete(self):
        assert self.table.count == 2
        new_row = {'Gemeindename': '------', 'Projektname': '-----',
                   'AGS': '0000', 'Gemeindetyp': 0}
        self.table.add(new_row)
        assert self.table.count == 3
        n = self.table.delete('"Gemeindename" = "------"')
        assert self.table.count == 2

    def test_pandas(self):
        a = self.table.to_pandas()

    def test_where(self):
        assert self.table.count == 2
        self.table.where = '"Gemeindename" = "noch was"'
        assert self.table.count == 1
        self.table.where = '"Projektname" = "p"'
        assert self.table.count == 2
        self.table.where = '"Projektname" = "pups"'
        assert self.table.count == 0


if __name__ == "__main__":
    suite = unittest.makeSuite(GeopackageTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
