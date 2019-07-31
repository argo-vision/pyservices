import json
import unittest
from threading import Thread
from urllib.parse import urlencode
from wsgiref import simple_server

import requests

from pyservices.service_descriptors.frameworks import FalconApp
from pyservices.service_descriptors.generators import RestGenerator
from pyservices.utilities.exceptions import ClientException
from test.data_descriptors.meta_models import *
from test.service_descriptors.service import AccountManager

address = '0.0.0.0'
port = 8080
base_path = f'http://{address}:{port}/{AccountManager.service_base_path}'


class TestRestServer(unittest.TestCase):

    def setUp(self):
        service = AccountManager({})

        app_wrapper = FalconApp()  # TODO the only WSGI framework implemented
        app_wrapper.register_route(service)
        self.httpd = simple_server.make_server(address, port, app_wrapper.app)
        t = Thread(target=self.httpd.serve_forever)
        t.start()

        self.client_proxy = RestGenerator.get_client_proxy(address, str(port),
                                                           AccountManager)

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
        self.assertEqual(resp.status_code, 201)

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
        self.assertEqual(resp.status_code, 400)

    def testClientResourceGetCollection(self):
        coll = self.client_proxy.interfaces.account_interface.collect()
        for el in coll:
            self.assertTrue(isinstance(el, Account))

    def testClientResourceGetCollectionValidParams(self):
        valid_params = [
            {},  # match 0,1,3
            {'username': 'second_account'},  # match 1,2
            {'username': 'second_account', 'email': 'second@email.com'},  # match 2
            {'friends_number': 5443},  # match 3
            {'username': 'not_an_existent_username'},
            {'friends_number': 999999999}]
        coll = self.client_proxy.interfaces.account_interface.collect(valid_params[0])
        self.assertEqual(len(coll), 4)

        coll = self.client_proxy.interfaces.account_interface.collect(valid_params[1])
        self.assertEqual(len(coll), 2)
        for a in coll:
            self.assertEqual(a.username, 'second_account')

        coll = self.client_proxy.interfaces.account_interface.collect(valid_params[2])
        self.assertEqual(len(coll), 1)
        self.assertEqual(coll[0].email, 'second@email.com')

        coll = self.client_proxy.interfaces.account_interface.collect(valid_params[3])
        self.assertEqual(len(coll), 1)
        for a in coll:
            self.assertGreaterEqual(a.friends_number, 5443)

        coll = self.client_proxy.interfaces.account_interface.collect(valid_params[4])
        self.assertEqual(len(coll), 0)

        coll = self.client_proxy.interfaces.account_interface.collect(valid_params[5])
        self.assertEqual(len(coll), 0)

    def testClientResourceGetCollectionInvalidParams(self):
        illegal_params = [
            {'username': 'first_account', 'friends_number': 1234},
            {'email': 'third@email.com'},
            {'fake': '0&username=second_account&email&second@email.com'},
            'username=second_account&email&second@email.com']
        for i in range(2):
            try:
                self.client_proxy.interfaces.account_interface.collect(illegal_params[i])
            except ClientException:
                continue
            else:
                self.fail(f'{ClientException} is be expected.')

        for i in range(2, 4):
            try:
                self.client_proxy.interfaces.account_interface.collect(illegal_params[i])
            except TypeError:
                continue
            else:
                self.fail(f'{TypeError} is be expected.')

    def testClientResourceGetDetail(self):
        detail = self.client_proxy.interfaces.account_interface.detail(1)
        self.assertTrue(isinstance(detail, Account))

    def testClientResourceAdd(self):
        res_id = self.client_proxy.interfaces.account_interface.add(accounts[1])
        self.assertEqual(res_id, '123')

    def testClientResourceUpdate(self):
        ret = self.client_proxy.interfaces.account_interface.update(
            0, accounts[1])
        self.assertTrue(ret)

    def testClientResourceDelete(self):
        ret = self.client_proxy.interfaces.account_interface.delete(0)
        self.assertTrue(ret)

    def testClientRPCArgs(self):
        self.client_proxy.interfaces.notes_op.check_args(arg1='arg1', arg2='arg2')

    def testClientRPCReturnValue(self):
        note = self.client_proxy.interfaces.notes_op.get_note(note_id=0)
        self.assertEqual(note, 'my note')


if __name__ == '__main__':
    unittest.main()
