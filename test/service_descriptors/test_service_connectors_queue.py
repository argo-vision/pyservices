import os
import unittest
from threading import Thread
from unittest.mock import Mock
from wsgiref import simple_server

import pyservices.context.microservice_utils as config_utils
from pyservices.context import context
from pyservices.service_descriptors.WSGIAppWrapper import FalconWrapper
from pyservices.service_descriptors.proxy import create_service_connector
from pyservices.utils import queues
from pyservices.utils.exceptions import ClientException
from pyservices.utils.queues import Queue
from test.data_descriptors.meta_models import *
from test.service_descriptors.components.account_manager import AccountManager
from test.service_descriptors.components.service1 import Service1, note_mm
from test.service_descriptors.components.service4 import Service4

address = '0.0.0.0'
port = 8080
service_port = 8000
port_remote = 8081
base_path_service1 = f'http://{address}:{port}'
base_path_service2 = f'http://{address}:{port}'
base_path_service3 = f'http://{address}:{port_remote}'

service_base_path = f'http://{address}:{service_port}'


class ServiceConnectorTest(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")
    _old_environment = os.getenv("ENVIRONMENT")
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.service_descriptors.uservices'

    @classmethod
    def setUpClass(cls):
        config_utils._config_dir = cls._my_config_path
        os.environ["GAE_SERVICE"] = "micro-service-queue"
        os.environ['ENVIRONMENT'] = 'DEVELOPMENT'

    @classmethod
    def tearDownClass(cls):
        if cls._old_service_name:
            os.environ["GAE_SERVICE"] = cls._old_service_name
        else:
            os.environ.pop("GAE_SERVICE")
        if cls._old_environment:
            os.environ["ENVIRONMENT"] = cls._old_environment
        else:
            os.environ.pop("ENVIRONMENT")
        config_utils._config_dir = cls._old_config_dir

    def setUp(self):
        queues.get_queue = Mock()
        self.queue = Queue()
        queues.get_queue.return_value = self.queue

        service = Service4()
        app_wrapper = FalconWrapper()  # TODO the only WSGI framework implemented
        app_wrapper.register_route(service)
        self.httpd = simple_server.make_server(address, service_port, app_wrapper.app)
        t = Thread(target=self.httpd.serve_forever)
        t.start()

        self.service = service
        self.connector = create_service_connector(Service4, service_base_path)
        service.start()


    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def testClientEvent(self):
        context.context = Mock()
        context.context.get_component.return_value = self.connector
        first_event_id = self.connector.events.test_queue(arg1="test1", arg2="test2")

        self.assertEqual(self.queue._last_id, first_event_id)

    def testSequenceEvents(self):
        context.context = Mock()
        context.context.get_component.return_value = self.connector
        task1 = self.connector.events.test_queue(arg1="test1", arg2="test2")
        task2 = self.connector.events.test_queue(arg1="test1", arg2="test2")
        task3 = self.connector.events.test_queue(arg1="test1", arg2="test2")
        task4 = self.connector.events.test_queue(arg1="test1", arg2="test2")

        self.assertEqual(self.queue._last_id, task4)
