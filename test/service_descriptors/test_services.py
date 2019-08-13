import json
import os
import unittest
from threading import Thread
from urllib.parse import urlencode
from wsgiref import simple_server

import requests

from pyservices.context.microservice_utils import MicroserviceConfiguration
from pyservices.service_descriptors.WSGIAppWrapper import FalconWrapper
from pyservices.service_descriptors.interfaces import InterfaceOperationDescriptor
from pyservices.service_descriptors.proxy import create_service_connector
from test.data_descriptors.meta_models import *
from test.service_descriptors.components.service_exposition1 import ServiceEx1
from test.service_descriptors.components.service_exposition3 import ServiceEx3
from test.service_descriptors.service import AccountManager

address = '0.0.0.0'
port = 8080
base_path = f'http://{address}:{port}/{AccountManager.service_base_path}'


class TestRestServer(unittest.TestCase):

    def setUp(self):
        service = AccountManager()

        app_wrapper = FalconWrapper()  # TODO the only WSGI framework implemented
        app_wrapper.register_route(service)
        self.httpd = simple_server.make_server(address, port, app_wrapper.app)
        t = Thread(target=self.httpd.serve_forever)
        t.start()

        self.connector = create_service_connector(AccountManager, base_path)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def testHTTPGetResource(self):
        resp = requests.get(base_path + '/account-interface/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text,
                         '{"email": "second@email.com", "friends_number": 5443,'
                         ' "id": 2, "username": "second_account"}')

    def testHTTPGetResources(self):
        resp = requests.get(base_path + '/account-interface')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, '[{"email": "first@email.com", "friends_numb'
                                    'er": 2314, "id": 1, "username": "first_ac'
                                    'count"}, {"email": "second@email.com", "f'
                                    'riends_number": 5443, "id": 2, "username"'
                                    ': "second_account"}, {"email": "second223'
                                    '@email.com", "friends_number": 5443, "id"'
                                    ': 3, "username": "second_account"}, {"ema'
                                    'il": "third@email.com", "friends_number":'
                                    ' 34125, "id": 4, "username": "third_accou'
                                    'nt"}]')

    def testHTTPAddResource(self):
        str_account = '{"email" : "new@email.com","username" : "new account",' \
                      ' "friends_number": 1234}'
        resp = requests.put(base_path + '/account-interface/',
                            str_account.encode())
        # self.assertEqual(resp.status_code, 201) # FIXME actual test, fix in #23
        self.assertEqual(resp.status_code, 200)
    def testHTTPUpdateResource(self):
        str_account = '{"email" : "ed@email.com","username" : "edited account' \
                      '", "friends_number": 231}'
        resp = requests.post(base_path + '/account-interface/1',
                             str_account.encode())
        self.assertEqual(resp.status_code, 200)

    def testHTTPDeleteResource(self):
        resp = requests.delete(base_path + '/account-interface/1')
        self.assertEqual(resp.status_code, 200)

    def testHTTPRPCArgs(self):
        args_data = {
            "arg1": "arg1",
            "arg2": "arg2"
        }
        params = urlencode(args_data)
        resp = requests.get(base_path + '/notes-op/check-args',
                            params)
        self.assertEqual(resp.status_code, 200)

    def testHTTPRPCNoArgs(self):
        resp = requests.post(base_path + '/notes-op/no-args')
        self.assertEqual(resp.status_code, 200)

    def testHTTPReturnValue(self):
        params = {
            "note_id": 0,
        }
        resp = requests.post(base_path + '/notes-op/get-note',
                             json.dumps(params))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), 'my note')

    def testHTTPRPCBadRequest(self):
        args_data = {
            "note": "arg1"
        }
        params = urlencode(args_data)
        resp = requests.get(base_path + '/notes-op/check-args',
                            params)
        # self.assertEqual(resp.status_code, 400) # FIXME actual code #23
        self.assertEqual(resp.status_code, 500)

    def testHTTPRPCEmptyRequest(self):
        resp = requests.post(base_path + '/notes-op/empty')
        self.assertEqual(resp.status_code, 404)


class TestRestServerExposition(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")
    _old_config_dir = MicroserviceConfiguration._config_dir
    _my_config_path = 'test.service_descriptors.uservices'

    @classmethod
    def setUpClass(cls):
        MicroserviceConfiguration._config_dir = cls._my_config_path

    @classmethod
    def tearDownClass(cls):
        if cls._old_service_name:
            os.environ["GAE_SERVICE"] = cls._old_service_name
        else:
            os.environ.pop("GAE_SERVICE")
        MicroserviceConfiguration._config_dir = cls._old_config_dir

    def setUp(self):
        self.address = '0.0.0.0'
        self.port1 = 8080
        self.port3 = 8081
        self.base_path1 = f'http://{address}:{self.port1}/{ServiceEx1.service_base_path}'
        self.base_path3 = f'http://{address}:{self.port3}/{ServiceEx3.service_base_path}'
        self.service1 = ServiceEx1()
        self.service3 = ServiceEx3()

        self.app_wrapper1 = FalconWrapper()  # TODO the only WSGI framework implemented
        self.app_wrapper3 = FalconWrapper()  # TODO the only WSGI framework implemented

    def tearDown(self):
        self.httpd1.shutdown()
        self.httpd1.server_close()
        self.httpd3.shutdown()
        self.httpd3.server_close()

    def testSelectiveExpositionDevelopment(self):
        self._put_env_and_start_server('DEVELOPMENT')
        self.assertTrue(requests.post(f'{self.base_path1}/expo/my-dep-op').json())
        self.assertTrue(requests.post(f'{self.base_path1}/expo/my-forbidden-op').json())
        self.assertTrue(requests.post(f'{self.base_path3}/expo/my-op').json())
        self.assertTrue(requests.post(f'{self.base_path3}/expo/my-mandatory-op').json())

    def testSelectiveExpositionProductionForbidden(self):
        self._put_env_and_start_server('PRODUCTION')
        self.assertEqual(
            requests.post(
                f'{self.base_path1}/expo/my-forbidden-op').status_code,
            404)

    def testSelectiveExpositionProductionMandatory(self):
        self._put_env_and_start_server('PRODUCTION')
        self.assertEqual(
            requests.post(
                f'{self.base_path3}/expo/my-mandatory-op').status_code,
            200)

    def testSelectiveExpositionProductionOnDependencyPresent(self):
        self._put_env_and_start_server('PRODUCTION')
        self.assertEqual(
            requests.post(
                f'{self.base_path3}/expo/my-op').status_code,
            404)

    def testSelectiveExpositionProductionOnDependencyNotPresent(self):
        self._put_env_and_start_server('PRODUCTION')
        self.assertEqual(
            requests.post(
                f'{self.base_path1}/expo/my-dep-op').status_code,
            200)

    def _put_env_and_start_server(self, env):
        os.environ['environment'] = env

        os.environ["GAE_SERVICE"] = "micro-service1"
        self.app_wrapper1.register_route(self.service1)
        os.environ["GAE_SERVICE"] = "micro-service3"
        self.app_wrapper3.register_route(self.service3)
        self.httpd1 = simple_server.make_server(self.address,
                                                self.port1,
                                                self.app_wrapper1.app)
        self.httpd3 = simple_server.make_server(self.address,
                                                self.port3,
                                                self.app_wrapper3.app)
        t = Thread(target=self.httpd1.serve_forever)
        t.start()
        t = Thread(target=self.httpd3.serve_forever)
        t.start()


if __name__ == '__main__':
    unittest.main()
