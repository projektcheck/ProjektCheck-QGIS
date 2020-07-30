import unittest

import test_init
import test_main_widget
import test_project
from projektcheck.base.tests import test_backend, test_project_management


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    # add tests to the test suite
    suite.addTests(loader.loadTestsFromModule(test_init))
    suite.addTests(loader.loadTestsFromModule(test_main_widget))
    suite.addTests(loader.loadTestsFromModule(test_project))
    suite.addTests(loader.loadTestsFromModule(test_backend))
    suite.addTests(loader.loadTestsFromModule(test_project_management))
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)