import unittest

from pyservices.context.microservice_utils import MicroServiceConfiguration


class MicroServicesTestCase(unittest.TestCase):
    def test_microserivces_list(self):
        configuration = {
            "a": {
                "services": [],
                "PORT": 5009,
                "address": "localhost"
            },
            "c": {
                "services": [],
                "PORT": 5009,
                "address": "localhost"
            },
            "b": {
                "services": [],
                "PORT": 5009,
                "address": "localhost"
            },
        }

        c = MicroServiceConfiguration(configuration, "a")

        microservices = c.microservices_names()
        self.assertEqual(["a", "b", "c"], sorted(microservices))

    def test_microservices_not_existent(self):
        configuration = {}
        self.assertRaises(ValueError, MicroServiceConfiguration, configuration, "a")

    def test_microservices_address(self):
        configuration = {"a": {"port": "1000", "address": "localhost"}}
        c = MicroServiceConfiguration(configuration, "a")

        self.assertEqual("localhost:1000", c.address())

    def test_find_service(self):
        configuration = {"a": {"services": ["b"]}}
        c = MicroServiceConfiguration(configuration, "a")

        self.assertEqual("a", c.microservice_of("b"))

    def test_find_service_error(self):
        configuration = {"a": {}}
        c = MicroServiceConfiguration(configuration, "a")

        self.assertRaises(ValueError, c.microservice_of, "b")

    def test_service_address(self):
        configuration = {"a": {"services": ["b"], "port": "1000", "address": "localhost"}}
        c = MicroServiceConfiguration(configuration, "a")

        self.assertEqual("localhost:1000", c.address_of("b"))

    def test_microservice_services(self):
        configuration = {"a": {"services": ["b"], "port": "1000", "address": "localhost"}}
        c = MicroServiceConfiguration(configuration, "a")

        self.assertEqual(["b"], c.services())

