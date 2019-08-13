import os
import unittest

import pyservices.context.microservice_utils as config_utils
from test.context.uservices import get_path


class TestMicroservices(unittest.TestCase):
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

    def test_config_dict(self):
        config = config_utils.current_config()
        self.assertIsInstance(config, dict)
        for v in config.values():
            self.assertIsInstance(v, dict)

    def test_microservices_host(self):
        self.assertEqual('localhost:1234', config_utils.host('microservice1'))

    def test_service_host(self):
        self.assertEqual('localhost:7890', config_utils.host(get_path('service3')))

    def test_microservice_services(self):
        ss = config_utils.services('microservice2')
        self.assertEqual([get_path('service3')],
                         ss)
        ss = config_utils.services(get_path('service3'))
        self.assertEqual([get_path('service3')],
                         ss)

    def test_all_services(self):
        ss = config_utils.all_services()

        self.assertEqual([get_path('service1'), get_path('service2'),
                         get_path('service3')], ss)

    def test_current_microservice_name(self):
        self.assertEqual("microservice1", config_utils.current_microservice())

    def test_microservice_current_host(self):
        self.assertEqual('localhost:1234', config_utils.current_host())
