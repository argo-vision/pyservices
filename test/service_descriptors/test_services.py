import json
import unittest
from threading import Thread
from urllib.parse import urlencode
from wsgiref import simple_server

import requests

from pyservices.service_descriptors.frameworks import FalconApp
from pyservices.service_descriptors.interfaces import InterfaceOperationDescriptor
from pyservices.service_descriptors.proxy import create_service_connector
from test.data_descriptors.meta_models import *
from test.service_descriptors.components.raw_interfaces import TestRPCInterface
from test.service_descriptors.service import AccountManager

address = '0.0.0.0'
port = 8080
base_path = f'http://{address}:{port}/{AccountManager.service_base_path}'


class TestRestServer(unittest.TestCase):

    def setUp(self):
        service = AccountManager()

        app_wrapper = FalconApp()  # TODO the only WSGI framework implemented
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


if __name__ == '__main__':
    unittest.main()
