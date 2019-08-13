import unittest

from pyservices.context.dependencies import create_application
from pyservices.context.microservice_utils import MicroServiceConfiguration
from pyservices.service_descriptors.layer_supertypes import Service, ServiceOperationReference

Service._module_prefix = 'test.operation_reference.components'


def get_path(comp_name):
    base_path = 'test.operation_reference.components'
    return f'{base_path}.{comp_name}'


class TestOperations(unittest.TestCase):

    def setUp(self):
        self.configurations = {
            'micro-service1': {
                'services': [get_path('service1')],
                'address': 'localhost',
                'port': '1234'
            }
        }

    def testReferenceOperations(self):
        conf = MicroServiceConfiguration(self.configurations, 'micro-service1')
        app = create_application(conf)
        reference = ServiceOperationReference("service1", "Test", "test_method_reference")
        self.assertEqual(reference(), "Processecs")
