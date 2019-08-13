import os
import unittest

import pyservices.context.microservice_utils as config_utils
from pyservices.context.dependencies import dependent_services
from test.context.uservices import get_path


class TestDependencies(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.context.uservices'

    @classmethod
    def setUpClass(cls):
        os.environ["GAE_SERVICE"] = "MICROService1"
        config_utils._config_dir = cls._my_config_path

    @classmethod
    def tearDownClass(cls):
        if cls._old_service_name:
            os.environ["GAE_SERVICE"] = cls._old_service_name
        else:
            os.environ.pop("GAE_SERVICE")
        config_utils._config_dir = cls._old_config_dir

    def test_dependent_services(self):
        deps = dependent_services('microservice2')
        deps = dependent_services(get_path('service3'))
        self.fail()

    def test_dependent_remote_service(self):
        self.fail()
