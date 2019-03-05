import unittest
from urllib import request
import pyservices as ps
from pyservices import tools

from pyservices.layer_supertypes import Service
from pyservices.data_descriptors import MetaModel, StringField


# TODO refactor with requests instead of urllib.request
class TestRestServer(unittest.TestCase):

    def setUp(self):
        MetaModel.modelClasses = {}
        self.account_mm = MetaModel('Account',
                                    StringField('username'),
                                    StringField('email'))
        account_cls = self.account_mm.get_class()
        self.user_mm = MetaModel('User',
                                 StringField('username'),
                                 self.account_mm())
        self.accounts = accounts = [
            account_cls('first_account', 'first@email.com'),
            account_cls('second_account', 'second@email.com'),
            account_cls('third_account', 'third@email.com')]
        self.users = users = [self.user_mm.get_class()('first_user',
                                                       self.accounts[0])]

        class AccountManager(Service):
            base_path = 'account-manager'

            @ps.rest_collection(self.account_mm, produces=ps.JSON)
            def get_accounts(self):

                return accounts

            @ps.rest_detail(self.account_mm, produces=ps.JSON)
            def get_account(self, res_id):
                return accounts[int(res_id)]

            @ps.rest_collection(meta_model=self.user_mm, produces=ps.JSON,
                                uri='utenti')
            def get_users(self):
                return users

            @ps.rest_add(self.account_mm)
            def add_account(self, account):
                accounts.append(account)

            @ps.rest_update(self.account_mm)
            def update_account(self, res_id, account):
                del accounts[int(res_id)]
                accounts.append(account)

            @ps.rest_delete(self.account_mm)
            def delete_account(self, res_id):
                del accounts[int(res_id)]

        self.AccountManager = AccountManager

        try:
            self.process, self.httpd = tools.rest_server(
                self.AccountManager({
                    'port': 7890,
                    'framework': ps.frameworks.FALCON}))
        except Exception as e:
            self.fail(e)

    def tearDown(self):
        self.httpd.server_close()
        self.process.kill()

    def testRESTGetResource(self):
        resp = request.urlopen(
            'http://localhost:7890/account-manager/accounts/1')
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.read().decode(),
                         '{"email": "second@email.com", "username": "second_acc'
                         'ount"}')

    def testRESTGetResources(self):
        # TODO check best practices for testing rest API server
        resp = request.urlopen(
            'http://localhost:7890/account-manager/accounts')
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.read().decode(),
                         '[{"email": "first@email.com", "username": "first_acco'
                         'unt"}, {"email": "second@email.com", "username": "sec'
                         'ond_account"}, {"email": "third@email.com", "username'
                         '": "third_account"}]')
        user_request = request.urlopen(
            'http://localhost:7890/account-manager/utenti')
        self.assertEqual(user_request.status, 200)
        self.assertEqual(user_request.read().decode(),
                         '[{"account": {"email": "first@email.com", "username":'
                         ' "first_account"}, "username": "first_user"}]')

    def testRESTAddResource(self):
        str_account = '{"email" : "new@email.com","username" : "new account"}'
        account_request = request.Request(
            'http://localhost:7890/account-manager/accounts/',
            method='PUT', data=str_account.encode())
        resp = request.urlopen(account_request)
        self.assertEqual(resp.status, 201)

    def testRESTUpdateResource(self):
        str_account = '{"email" : "ed@email.com","username" : "edited account"}'
        account_request = request.Request(
            'http://localhost:7890/account-manager/accounts/1',
            method='POST', data=str_account.encode())
        resp = request.urlopen(account_request)
        self.assertEqual(resp.status, 200)

    def testRESTDeleteResource(self):
        account_request = request.Request(
            'http://localhost:7890/account-manager/accounts/2',
            method='DELETE')
        resp = request.urlopen(account_request)
        self.assertEqual(resp.status, 200)

    def testRestClient(self):
        # TODO
        pass
        # try:
        #     client_proxy = tools.rest_client(
        #         self.AccountManager(
        #             {'framework': ps.frameworks.FALCON}))
        # except Exception as e:
        #     self.fail(e)
        #
        # proxy_res = client_proxy.get_collection(self.account_mm)
        # self.assertListEqual(proxy_res, self.accounts)
        # proxy_res = client_proxy.get_detail(self.account_mm, 2)
        # self.assertEqual(proxy_res, self.accounts[2])
        # proxy_res = client_proxy.get_list(self.user_mm)
        # self.assertListEqual(proxy_res, self.users)


if __name__ == '__main__':
    unittest.main()
