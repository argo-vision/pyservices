import unittest
from unittest.mock import Mock

import pyservices.context.microservice_utils as config_utils
from pyservices.context import dependencies
from pyservices.context import microservice_utils
from pyservices.utils.url_composer import DefaultUrlComposer, LocalhostUrlComposer


class TestUrlComposer(unittest.TestCase):
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.context.uservices'

    @classmethod
    def setUpClass(cls):
        config_utils._config_dir = cls._my_config_path

    @classmethod
    def tearDownClass(cls):
        config_utils._config_dir = cls._old_config_dir

    def setUp(self):
        self.service = Mock()
        microservice_utils.current_host = Mock()
        microservice_utils.current_host.return_value = 'localhost:8000'

        dependencies.get_service_class = Mock()
        dependencies.get_service_class.return_value = Mock()
        dependencies.get_service_class.return_value.service_base_path = 'service-1'

    def testLocalhostUrlComposerHTTP(self):
        self.assertEqual('http://localhost:8000/service-1',
                         LocalhostUrlComposer.get_http_url(self.service))
        self.assertEqual('http://localhost:8000/service-1',
                         LocalhostUrlComposer.get_https_url(self.service))

    def testDefaultUrlComposerHTTP(self):
        self.assertEqual('http://localhost:1234',
                         DefaultUrlComposer.get_http_url('microservice1'))
        self.assertEqual('https://localhost:1234',
                         DefaultUrlComposer.get_https_url('microservice1'))

    def testDefaultUrlComposerHTTPS(self):
        self.assertEqual('http://localhost:7890',
                         DefaultUrlComposer.get_http_url('microservice2'))
        self.assertEqual('https://localhost:7890',
                         DefaultUrlComposer.get_https_url('microservice2'))

    def ignored_testGCloudUrlComposer(self):
        self.fail("TODO")
