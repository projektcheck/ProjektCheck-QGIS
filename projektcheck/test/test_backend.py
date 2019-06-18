# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest

from pctools.backend.geopackage import Geopackage


class GeopackageTest(unittest.TestCase):
    """Test geopackage backend"""

    def setUp(self):
        self.backend = Geopackage()
        self.table = self.backend.get_table('Projektrahmendaten',
                                            'Definition_Projekt')

    def tearDown(self):
        pass

    def test_iter(self):
        for row in self.table:
            print(row)
        for row in self.table:
            print(row)

    def test_pandas(self):
        a = self.table.to_pandas()


if __name__ == "__main__":
    suite = unittest.makeSuite(GeopackageTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
