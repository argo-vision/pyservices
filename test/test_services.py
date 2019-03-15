import unittest
import requests
import pyservices as ps

from pyservices.layer_supertypes import Service
from pyservices.interfaces import RestfulResource
from pyservices.data_descriptors import MetaModel, StringField


# TODO refactor
class TestRestServer(unittest.TestCase):

    def setUp(self):
        MetaModel.modelClasses = {}
        self.note_mm = NoteMM = MetaModel('Note',
                                          StringField('title'),
                                          StringField('content'))
        self.account_mm = AccountMM = MetaModel('Account',
                                                StringField('username'),
                                                StringField('email'))
        account_cls = self.account_mm.get_class()
        self.user_mm = UserMM = MetaModel('User',
                                          StringField('username'),
                                          self.account_mm())
        self.accounts = accounts = [
            account_cls('first_account', 'first@email.com'),
            account_cls('second_account', 'second@email.com'),
            account_cls('third_account', 'third@email.com')]
        self.users = users = [self.user_mm.get_class()('first_user',
                                                       self.accounts[0])]
        self.notes = notes = [
            NoteMM.get_class()('FirstTitle', 'Content1234')]

        class AccountManager(Service):
            base_path = 'account-manager'

            class Note(ps.interfaces.RestfulResource):
                meta_model = NoteMM

                def collection(self):
                    return self.notes

            class Account(ps.interfaces.RestfulResource):
                meta_model = AccountMM
                resource_path = 'accounts'  # useless
                codec = ps.JSON  # useless

                # TODO static method?
                @staticmethod
                def collection():
                    return accounts

                @staticmethod
                def detail(res_id):
                    return accounts[int(res_id)]

                @staticmethod
                def add(account):
                    accounts.append(account)

                @staticmethod
                def update(res_id, account):
                    del accounts[int(res_id)]
                    accounts.append(account)

                @staticmethod
                def delete(res_id):
                    del accounts[int(res_id)]

        self.AccountManager = AccountManager
        account_manager_service = self.AccountManager({
                    'port': 7890,
                    'framework': ps.frameworks.FALCON})
        try:
            # TODO rest service the same
            self.thread, self.httpd = account_manager_service.rest_server()

            # TODO check stato opp no
            self.client_proxy = account_manager_service.rest_client()
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
                         '{"email": "second@email.com", "username": "second_acc'
                         'ount"}')

    def testRESTGetResources(self):
        resp = requests.get(
            'http://localhost:7890/account-manager/accounts')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text,
                         '[{"email": "first@email.com", "username": "first_acco'
                         'unt"}, {"email": "second@email.com", "username": "sec'
                         'ond_account"}, {"email": "third@email.com", "username'
                         '": "third_account"}]')

    def testRESTAddResource(self):
        str_account = '{"email" : "new@email.com","username" : "new account"}'
        resp = requests.put('http://localhost:7890/account-manager/accounts/',
                            str_account.encode())
        self.assertEqual(resp.status_code, 201)

    def testRESTUpdateResource(self):
        str_account = '{"email" : "ed@email.com","username" : "edited account"}'
        resp = requests.post('http://localhost:7890/account-manager/accounts/1',
                             str_account.encode())
        self.assertEqual(resp.status_code, 200)

    def testRESTDeleteResource(self):
        resp = requests.delete(
            'http://localhost:7890/account-manager/accounts/1')
        self.assertEqual(resp.status_code, 200)

    def testClientGetCollection(self):
        coll = self.client_proxy.interfaces['accounts'].get_collection()
        for el in coll:
            self.assertTrue(isinstance(el, self.account_mm.get_class()))

    def testClientGetDetail(self):
        detail = self.client_proxy.interfaces['accounts'].get_detail(1)
        self.assertTrue(isinstance(detail, self.account_mm.get_class()))

    def testClientAdd(self):
        ret = self.client_proxy.interfaces['accounts'].add(self.accounts[1])
        self.assertTrue(ret)

    def testClientUpdate(self):
        ret = self.client_proxy.interfaces['accounts'].update(
            0, self.accounts[1])
        self.assertTrue(ret)

    def testClientDelete(self):
        ret = self.client_proxy.interfaces['accounts'].delete(0)
        self.assertTrue(ret)


if __name__ == '__main__':
    unittest.main()
