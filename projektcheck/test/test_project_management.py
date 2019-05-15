
# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'
__copyright__ = 'Copyright 2019, GGR Planungsbuero'

import unittest


class ProjectTest(unittest.TestCase):
    """Test projects"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create(self):
        pass

    def test_delete(self):
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(ProjectTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
