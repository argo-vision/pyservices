import unittest

from pyservices.utils.url_composer import DefaultUrlComposer
import pyservices.context.microservice_utils as config_utils


class TestUrlComposer(unittest.TestCase):
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.context.uservices'

    @classmethod
    def setUpClass(cls):
        config_utils._config_dir = cls._my_config_path

    @classmethod
    def tearDownClass(cls):
        config_utils._config_dir = cls._old_config_dir

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
