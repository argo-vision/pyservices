import os
import unittest

import pyservices.context.microservice_utils as config_utils
from pyservices.context.dependencies import create_application
from pyservices.service_descriptors.WSGIAppWrapper import WSGIAppWrapper


class TestContext(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.context.uservices'

    @classmethod
    def setUpClass(cls):
        config_utils._config_dir = cls._my_config_path

    @classmethod
    def tearDownClass(cls):
        if cls._old_service_name:
            os.environ["GAE_SERVICE"] = cls._old_service_name
        else:
            os.environ.pop("GAE_SERVICE")
        config_utils._config_dir = cls._old_config_dir

    def testCreateApplication(self):
        os.environ["GAE_SERVICE"] = "microservice1"
        app = create_application()
        self.assertTrue(isinstance(app, WSGIAppWrapper))
        os.environ["GAE_SERVICE"] = "microservice2"
        app = create_application()
        self.assertTrue(isinstance(app, WSGIAppWrapper))
