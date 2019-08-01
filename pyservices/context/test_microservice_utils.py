import unittest

from .microservice_utils import MicroServicesConfiguration


class MicroServicesTestCase(unittest.TestCase):
    def test_microserivces_list(self):
        configuration = {
            "a": {
                "components": [],
                "PORT": 5009,
                "address": "localhost"
            },
            "c": {
                "components": [],
                "PORT": 5009,
                "address": "localhost"
            },
            "b": {
                "components": [],
                "PORT": 5009,
                "address": "localhost"
            },
        }

        c = MicroServicesConfiguration(configuration)

        microservices = c.microservices_names()
        self.assertEqual(["a", "b", "c"], sorted(microservices))

    def test_microservices_address_error(self):
        configuration = {}
        c = MicroServicesConfiguration(configuration)

        self.assertRaises(ValueError, c.microservice_address, "not exists")

    def test_microservices_address(self):
        configuration = {"a": {"port": "1000", "address": "localhost"}}
        c = MicroServicesConfiguration(configuration)

        self.assertEqual("localhost:1000", c.microservice_address("a"))

    def test_find_service(self):
        configuration = {"a": {"components": ["b"]}}
        c = MicroServicesConfiguration(configuration)

        self.assertEqual("a", c.microservice_of("b"))

    def test_find_service_error(self):
        configuration = {}
        c = MicroServicesConfiguration(configuration)

        self.assertRaises(ValueError, c.microservice_of, "b")

    def test_service_address(self):
        configuration = {"a": {"components": ["b"], "port": "1000", "address": "localhost"}}
        c = MicroServicesConfiguration(configuration)

        self.assertEqual("localhost:1000", c.service_address("b"))

    def test_microservice_components_error(self):
        configuration = {}
        c = MicroServicesConfiguration(configuration)

        self.assertRaises(ValueError, c.microservice_services, "b")

    def test_microservice_components(self):
        configuration = {"a": {"components": ["b"], "port": "1000", "address": "localhost"}}
        c = MicroServicesConfiguration(configuration)

        self.assertEqual(["b"], c.microservice_services("a"))

    def test_microservice_configuration(self):
        configuration = {"a": {"components": ["b"], "port": "1000", "address": "localhost"}}
        c = MicroServicesConfiguration(configuration)
        self.assertDictEqual(configuration["a"], c.microservice_configuration("a"))

    def test_microservice_configuration_error(self):
        configuration = {}
        c = MicroServicesConfiguration(configuration)
        self.assertRaises(ValueError, c.microservice_configuration, "a")
