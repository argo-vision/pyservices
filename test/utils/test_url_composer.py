import unittest

from pyservices.context.microservice_utils import MicroserviceConfiguration
from pyservices.utils.url_composer import DefaultUrlComposer
from test.context.components.configuration import configurations, get_path


class TestUrlComposer(unittest.TestCase):
    def testDefaultUrlComposer(self):
        msconf = MicroserviceConfiguration('micro-service1')
        url_composer = DefaultUrlComposer(msconf)
        self.assertEqual(url_composer.get_http_url(get_path('service1')),
                         'http://localhost:1234')
        self.assertEqual(url_composer.get_https_url(get_path('service1')),
                         'https://localhost:1234')
        self.assertEqual(url_composer.get_http_url(get_path('service3')),
                         'http://localhost:7890')
        self.assertEqual(url_composer.get_https_url(get_path('service3')),
                         'https://localhost:7890')

    def ignored_testGCloudUrlComposer(self):
        self.fail("TODO")
