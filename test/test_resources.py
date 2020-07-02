# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'

import unittest

from qgis.PyQt.QtGui import QIcon


class ProjektCheckResourcesTest(unittest.TestCase):
    '''Test resources'''

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_icon_png(self):
        '''test that icon is in resource file'''
        path = ':/plugins/ProjektCheck/icon.png'
        icon = QIcon(path)
        self.assertFalse(icon.isNull())

if __name__ == "__main__":
    suite = unittest.makeSuite(ProjektCheckResourcesTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)



