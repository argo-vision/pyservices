import os
import unittest
from unittest.mock import Mock

from pyservices.service_descriptors.interfaces import \
    InterfaceOperationDescriptor
from pyservices.utils import queues
from pyservices.utils.queues import Queue
from test.service_descriptors.components.raw_interfaces import TestEventInterface
from test.service_descriptors.components.raw_interfaces import TestRPCInterface, \
    TestRestInterface


class ServiceConnectorTest(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")

    @classmethod
    def setUpClass(cls):
        os.environ["GAE_SERVICE"] = "MICROService1"

    @classmethod
    def tearDownClass(cls):
        if cls._old_service_name:
            os.environ["GAE_SERVICE"] = cls._old_service_name
        else:
            os.environ.pop("GAE_SERVICE")

    def testRestInterfaceHttpOperations(self):
        service = Mock()
        service.service_base_path = 'service_base_path'
        iface = TestRestInterface(service)
        ops = iface._get_http_operations()
        for op in ops:
            self.assertIsInstance(op, InterfaceOperationDescriptor)

    def testRPCInterfaceHttpOperations(self):
        service = Mock()
        service.service_base_path = 'service_base_path'
        iface = TestRPCInterface(service)
        ops = iface._get_http_operations()
        for op in ops:
            self.assertIsInstance(op, InterfaceOperationDescriptor)

    def testEventInterfaceHttpOperations(self):

        queues.get_queue = Mock()
        queues.get_queue.return_value = Queue()

        service = Mock()
        service.service_base_path = 'service_base_path'
        iface = TestEventInterface(service)
        ops = iface._get_http_operations()
        for op in ops:
            self.assertIsInstance(op, InterfaceOperationDescriptor)
