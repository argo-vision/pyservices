import unittest
from pyservices.context import create_application
from pyservices.service_descriptors.generators import RestGenerator
from test.test_context.my_service import MyService

configuration = {
    'components': ['test_context.my_service']
}


class TestContext(unittest.TestCase):

    def setUp(self):
        create_application(configuration)

    def test_client_init(self):
        client = RestGenerator.get_client_proxy('0.0.0.0', '7890', MyService)
        self.assertTrue(client.interfaces)
