import unittest

import requests

import pyservices as ps
from pyservices.data_descriptors.fields import MetaModel, StringField, \
    IntegerField
from pyservices.exceptions import ClientException
from pyservices.service_descriptors.generators import RestGenerator
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RestResource
from pyservices.service_descriptors.frameworks import FALCON


# TODO refactor # test limit cases (0, 1, N)
class TestRestServer(unittest.TestCase):

    def setUp(self):
        MetaModel.modelClasses = {}
        self.note_mm = NoteMM = MetaModel('Note',
                                          StringField('title'),
                                          StringField('content'),
                                          primary_key_name='title')
        self.account_mm = AccountMM = MetaModel('Account',
                                                StringField('username'),
                                                StringField('email'),
                                                IntegerField('friends_number'),
                                                IntegerField('id'),
                                                primary_key_name='id')
        account_cls = self.account_mm.get_class()
        self.user_mm = UserMM = MetaModel('User',
                                          StringField('username'),
                                          self.account_mm())
        self.accounts = accounts = [
            account_cls('first_account', 'first@email.com', 2314, 1),
            account_cls('second_account', 'second@email.com', 5443, 2),
            account_cls('second_account', 'second223@email.com', 5443, 3),
            account_cls('third_account', 'third@email.com', 34125, 4)]
        self.users = users = [self.user_mm.get_class()('first_user',
                                                       self.accounts[0])]
        self.notes = notes = [
            NoteMM.get_class()('FirstTitle', 'Content1234')]

        class AccountManager(Service):

            class Note(RestResource):
                meta_model = NoteMM

                def collect(self):
                    return self.notes

            class Account(RestResource):
                meta_model = AccountMM
                resource_path = 'accounts'  # default
                codec = ps.JSON  # default

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
                    accounts.append(account)
                    return res_id

                def update(self, res_id, account):
                    del accounts[int(res_id)]
                    accounts.append(account)

                def delete(self, res_id):
                    del accounts[int(res_id)]

        self.AccountManager = AccountManager
        account_manager_service = self.AccountManager({
            'address': 'localhost',
            'port': '7890',
            'framework': FALCON,
            'service_base_path': 'account-manager'})
        RestGenerator._servers = {}
        try:
            self.thread, self.httpd = RestGenerator.generate_rest_server(
                account_manager_service)
            self.client_proxy = RestGenerator.get_client_proxy(
                'localhost', '7890', 'account-manager', AccountManager)
        except Exception as e:
            self.fail(e)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()

    def testRESTGetResource(self):
        resp = requests.get(
            'http://localhost:7890/account-manager/accounts/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text,
                         '{"email": "second@email.com", "friends_number": 5443,'
                         ' "id": 2, "username": "second_account"}')

    def testRESTGetResources(self):
        resp = requests.get(
            'http://localhost:7890/account-manager/accounts')
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

    def testRESTAddResource(self):
        str_account = '{"email" : "new@email.com","username" : "new account",' \
                      ' "friends_number": 1234}'
        resp = requests.put('http://localhost:7890/account-manager/accounts/',
                            str_account.encode())
        self.assertEqual(resp.status_code, 201)

    def testRESTUpdateResource(self):
        str_account = '{"email" : "ed@email.com","username" : "edited account' \
                      '", "friends_number": 231}'
        resp = requests.post('http://localhost:7890/account-manager/accounts/1',
                             str_account.encode())
        self.assertEqual(resp.status_code, 200)

    def testRESTDeleteResource(self):
        resp = requests.delete(
            'http://localhost:7890/account-manager/accounts/1')
        self.assertEqual(resp.status_code, 200)

    def testClientGetCollection(self):
        coll = self.client_proxy.interfaces.accounts.collect()
        # TODO len
        for el in coll:
            self.assertTrue(isinstance(el, self.account_mm.get_class()))

    def testClientGetCollectionValidParams(self):
        valid_params = [
            {},  # match 0,1,3
            {'username': 'second_account'},  # match 1,2
            {'username': 'second_account', 'email': 'second@email.com'},  # match 2
            {'friends_number': 5443},  # match 3
            {'username': 'not_an_existent_username'},
            {'friends_number': 999999999}]
        coll = self.client_proxy.interfaces.accounts.collect(valid_params[0])
        self.assertEqual(len(coll), 4)

        coll = self.client_proxy.interfaces.accounts.collect(valid_params[1])
        self.assertEqual(len(coll), 2)
        for a in coll:
            self.assertEqual(a.username, 'second_account')

        coll = self.client_proxy.interfaces.accounts.collect(valid_params[2])
        self.assertEqual(len(coll), 1)
        self.assertEqual(coll[0].email, 'second@email.com')

        coll = self.client_proxy.interfaces.accounts.collect(valid_params[3])
        self.assertEqual(len(coll), 1)
        for a in coll:
            self.assertGreaterEqual(a.friends_number, 5443)

        coll = self.client_proxy.interfaces.accounts.collect(valid_params[4])
        self.assertEqual(len(coll), 0)

        coll = self.client_proxy.interfaces.accounts.collect(valid_params[5])
        self.assertEqual(len(coll), 0)

    def testClientGetCollectionInvalidParams(self):
        illegal_params = [
            {'username': 'first_account', 'friends_number': 1234},
            {'email': 'third@email.com'},
            {'fake': '0&username=second_account&email&second@email.com'},
            'username=second_account&email&second@email.com']
        for i in range(2):
            try:
                self.client_proxy.interfaces.accounts.collect(illegal_params[i])
            except ClientException:
                continue
            else:
                self.fail(f'{ClientException} is be expected.')

        for i in range(2, 4):
            try:
                self.client_proxy.interfaces.accounts.collect(illegal_params[i])
            except TypeError:
                continue
            else:
                self.fail(f'{TypeError} is be expected.')

    def testClientGetDetail(self):
        detail = self.client_proxy.interfaces.accounts.detail(1)
        self.assertTrue(isinstance(detail, self.account_mm.get_class()))

    def testClientAdd(self):
        res_id = self.client_proxy.interfaces.accounts.add(self.accounts[1])
        self.assertEqual(res_id, '123')

    def testClientUpdate(self):
        ret = self.client_proxy.interfaces.accounts.update(
            0, self.accounts[1])
        self.assertTrue(ret)

    def testClientDelete(self):
        ret = self.client_proxy.interfaces.accounts.delete(0)
        self.assertTrue(ret)




if __name__ == '__main__':
    unittest.main()
