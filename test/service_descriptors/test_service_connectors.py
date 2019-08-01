import unittest

from threading import Thread
from wsgiref import simple_server

from pyservices.service_descriptors.frameworks import FalconApp
from pyservices.service_descriptors.service_connector import create_service_connector
from pyservices.context.dependencies import create_application

from test.service_descriptors.components.service1 import Service1, note_mm
from test.service_descriptors.components.service2 import Service2
from test.service_descriptors.components.service3 import Service3

address = '0.0.0.0'
port = 8080
port_remote = 8081
base_path_service1 = f'http://{address}:{port}/{Service1.service_base_path}'
base_path_service2 = f'http://{address}:{port}/{Service2.service_base_path}'
base_path_service3 = f'http://{address}:{port_remote}/{Service3.service_base_path}'


def get_path(comp_name):
    path = 'test.service_descriptors.components'
    return f'{path}.{comp_name}'


configurations = {
    'micro-service1': {
        'services': [get_path('service1'), get_path('service2')]
    },
    'micro-service2': {
        'services': [get_path('service3')]
    }
}


class ServiceConnectorTest(unittest.TestCase):

    def testServiceConnectorLocal(self):
        connector = create_service_connector(Service1(), 'local')
        note = connector.notes.detail(123)
        self.assertTrue(isinstance(note, note_mm.get_class()))
        content = connector.notes_op.read_note()
        self.assertEqual(note.content, content)

    def testServiceConnectorRemote(self):
        service = Service1()
        app_wrapper = FalconApp()
        app_wrapper.register_route(service)
        httpd = simple_server.make_server(address, port, app_wrapper.app)
        t = Thread(target=httpd.serve_forever)
        t.start()
        connector = create_service_connector(Service1(), base_path_service1)
        note = connector.notes.detail(123)
        self.assertTrue(isinstance(note, note_mm.get_class()))
        content = connector.notes_op.read_note()
        self.assertEqual(note.content, content)
        httpd.shutdown()
        httpd.server_close()

    def testLocalCall(self):
        app_local = create_application(configurations['micro-service1'])
        connector = create_service_connector(Service2(), 'local')
        httpd = simple_server.make_server(address, port, app_local)

        self.service.dependencies['local_service'].my_call(123)
        httpd.shutdown()
        httpd.server_close()

    def testRemoteCall(self):
        app_remote = create_application(configurations)
        self.service.dependencies['remote_service'].my_call(123)

