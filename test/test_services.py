import unittest

import requests

import pyservices as ps
from pyservices.exceptions import ClientException
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import HTTPOperation
from pyservices.service_descriptors.generators import RestGenerator
from pyservices.service_descriptors.interfaces import *
from test.meta_models import *

base_path = 'http://localhost:7890/account-manager'


class AccountManager(Service):
    service_base_path = 'account-manager'

    class Note(RestResourceInterface):
        meta_model = NoteMM

        def collect(self):
            return notes

    class Account(RestResourceInterface):
        meta_model = AccountMM
        if_path = 'account-interface'  # not default behaviour

        def collect(self):
            return accounts

        def collect_username(self, username=None):
            return [a for a in accounts
                    if a.username == username]

        def collect_username_email(self, username, email=None):
            return [a for a in accounts
                    if a.username == username and a.email == email]

        def collect_friends(self, friends_number=None):
            return [a for a in accounts
                    if a.friends_number > int(friends_number)]

        def detail(self, res_id):
            return accounts[int(res_id)]

        def add(self, account):
            res_id = '123'
            assert type(account) is Account
            return res_id

        def update(self, res_id, account):
            assert type(res_id) is int
            assert type(account) is Account

        def delete(self, res_id):
            assert type(res_id) is int

    # TODO think to some tests
    class NotesOperations(RPCInterface):
        if_path = 'notes-operations'

        @HTTPOperation(method='GET', path='read-note')
        def readnote(self, req, res):
            # give some flexibility with req e res? TODO I1
            # res.body = f'{note.title - note.content}'  # TODO I1
            pass

        @HTTPOperation(method='POST')
        def randomnote(self, req, res):
            pass

        def _get_note(self, note_id):
            return notes[note_id]


class TestRestServer(unittest.TestCase):

    def setUp(self):
        self.account_manager_service = AccountManager({
            'address': 'localhost',
            'port': '7890',
            'framework': ps.frameworks.FALCON,
            'service_base_path': 'account-manager'})
        try:
            self.account_manager_service.start()
            self.client_proxy = RestGenerator.get_client_proxy(
                'localhost', '7890', 'account-manager', AccountManager)
        except Exception as e:
            self.fail(e)

    def tearDown(self):
        self.account_manager_service.stop()

    def testHTTPGetResource(self):
        resp = requests.get(
            'http://localhost:7890/account-manager/account-interface/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text,
                         '{"email": "second@email.com", "friends_number": 5443,'
                         ' "id": 2, "username": "second_account"}')

    def testHTTPGetResources(self):
        resp = requests.get(
            'http://localhost:7890/account-manager/account-interface')
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
        resp = requests.delete(
            base_path + '/account-interface/1')
        self.assertEqual(resp.status_code, 200)

    def testHTTPRPC(self):
        resp = requests.post(base_path + '/notes-operations/randomnote')
        # self.assertRaises(resp.json())  # TODO discuss type negotiation, test data I1
        self.assertEqual(resp.status_code, 200)
        resp = requests.get(base_path + '/notes-operations/read-note')
        # self.assertRaises(resp.json())  # TODO discuss type negotiation, test data I1
        self.assertEqual(resp.status_code, 200)

    def testClientResourceGetCollection(self):
        coll = self.client_proxy.interfaces.REST.account_interface.collect()
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
        coll = self.client_proxy.interfaces.REST.account_interface.collect(valid_params[0])
        self.assertEqual(len(coll), 4)

        coll = self.client_proxy.interfaces.REST.account_interface.collect(valid_params[1])
        self.assertEqual(len(coll), 2)
        for a in coll:
            self.assertEqual(a.username, 'second_account')

        coll = self.client_proxy.interfaces.REST.account_interface.collect(valid_params[2])
        self.assertEqual(len(coll), 1)
        self.assertEqual(coll[0].email, 'second@email.com')

        coll = self.client_proxy.interfaces.REST.account_interface.collect(valid_params[3])
        self.assertEqual(len(coll), 1)
        for a in coll:
            self.assertGreaterEqual(a.friends_number, 5443)

        coll = self.client_proxy.interfaces.REST.account_interface.collect(valid_params[4])
        self.assertEqual(len(coll), 0)

        coll = self.client_proxy.interfaces.REST.account_interface.collect(valid_params[5])
        self.assertEqual(len(coll), 0)

    def testClientResourceGetCollectionInvalidParams(self):
        illegal_params = [
            {'username': 'first_account', 'friends_number': 1234},
            {'email': 'third@email.com'},
            {'fake': '0&username=second_account&email&second@email.com'},
            'username=second_account&email&second@email.com']
        for i in range(2):
            try:
                self.client_proxy.interfaces.REST.account_interface.collect(illegal_params[i])
            except ClientException:
                continue
            else:
                self.fail(f'{ClientException} is be expected.')

        for i in range(2, 4):
            try:
                self.client_proxy.interfaces.REST.account_interface.collect(illegal_params[i])
            except TypeError:
                continue
            else:
                self.fail(f'{TypeError} is be expected.')

    def testClientResourceGetDetail(self):
        detail = self.client_proxy.interfaces.REST.account_interface.detail(1)
        self.assertTrue(isinstance(detail, Account))

    def testClientResourceAdd(self):
        res_id = self.client_proxy.interfaces.REST.account_interface.add(accounts[1])
        self.assertEqual(res_id, '123')

    def testClientResourceUpdate(self):
        ret = self.client_proxy.interfaces.REST.account_interface.update(
            0, accounts[1])
        self.assertTrue(ret)

    def testClientResourceDelete(self):
        ret = self.client_proxy.interfaces.REST.account_interface.delete(0)
        self.assertTrue(ret)

    def testClientRPC(self):
        ret = self.client_proxy.interfaces.RPC.notes_operations.read_note()
        self.assertTrue(ret)
        ret = self.client_proxy.interfaces.RPC.notes_operations.randomnote()
        self.assertTrue(ret)

        # self.assertRaises(ret.data())  # TODO discuss type negotiation, test data I1


if __name__ == '__main__':
    unittest.main()
