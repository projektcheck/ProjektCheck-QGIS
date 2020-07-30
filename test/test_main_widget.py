# coding=utf-8
__author__ = 'Christoph Franke'
__license__ = 'GPL'

import unittest

from qgis.PyQt.QtGui import QIcon
from utilities import get_qgis_app
QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

from projektcheck.settings import settings
from projektcheck.main_widget import ProjektCheckControl


class ProjektCheckDockWidgetTest(unittest.TestCase):

    def setUp(self):
        self.dockwidget = ProjektCheckControl(iface=IFACE, canvas=CANVAS)
        self.dockwidget.setupUi()

    def tearDown(self):
        self.dockwidget.close()

    def test_dockwidget(self):
        self.dockwidget.ui.definition_button.click()

    def test_resources(self):
        # test that icon is in resource file
        path = ':/plugins/ProjektCheck/icon.png'
        icon = QIcon(path)
        self.assertFalse(icon.isNull())

if __name__ == "__main__":
    suite = unittest.makeSuite(ProjektCheckDockWidgetTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

