# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest

from pctools.backend.generic import Database


class GenericDatabaseTest(unittest.TestCase):

    def setUp(self):
        class Gen1DB(Database):
            ''''''
        class Gen2DB(Database):
            ''''''

        self.gen11 = Gen1DB()
        self.gen12 = Gen1DB()
        self.gen2 = Gen2DB()

    def tearDown(self):
        pass

    def test_singleton(self):
        self.assertEqual(id(self.gen11), id(self.gen12))
        self.assertNotEqual(id(self.gen11), id(self.gen2))


class GeopackageTest(unittest.TestCase):
    """Test geopackage backend"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_workspace(self):
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(GenericDatabaseTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
