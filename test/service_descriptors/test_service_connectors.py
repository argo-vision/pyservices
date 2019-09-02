import os
import unittest
from threading import Thread
from unittest.mock import Mock
from wsgiref import simple_server

import pyservices.context.microservice_utils as config_utils
from pyservices.context import context, Context
from pyservices.service_descriptors.WSGIAppWrapper import FalconWrapper
from pyservices.service_descriptors.proxy import create_service_connector
from pyservices.utils.exceptions import ClientException
from test.data_descriptors.meta_models import *
from test.service_descriptors.components.account_manager import AccountManager
from test.service_descriptors.components.service1 import Service1, note_mm

address = '0.0.0.0'
port = 8080
account_manager_port = 8000
port_remote = 8081
base_path_service1 = f'http://{address}:{port}'
base_path_service2 = f'http://{address}:{port}'
base_path_service3 = f'http://{address}:{port_remote}'

account_manager_base_path = f'http://{address}:{account_manager_port}'


class ServiceConnectorTest(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")
    _old_environment = os.getenv("ENVIRONMENT")
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.service_descriptors.uservices'

    @classmethod
    def setUpClass(cls):
        config_utils._config_dir = cls._my_config_path
        os.environ["GAE_SERVICE"] = "micro-service1"
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
        self.ctx = Context()
        service = AccountManager(self.ctx)
        app_wrapper = FalconWrapper()  # TODO the only WSGI framework implemented
        app_wrapper.register_route(service)
        self.httpd = simple_server.make_server(address, account_manager_port, app_wrapper.app)
        t = Thread(target=self.httpd.serve_forever)
        t.start()

        self.service = service
        self.connector = create_service_connector(AccountManager, account_manager_base_path)

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def testServiceConnectorLocal(self):
        s = Service1(self.ctx)
        connector = create_service_connector(Service1, s)
        note = connector.mynotes.detail(123)
        self.assertIsInstance(note, note_mm.get_class())

        notes = connector.mynotes.collect()

        self.assertIsInstance(notes, list)
        self.assertEqual(notes[0], note)

        content = connector.notes_op.read_note()
        self.assertEqual(note.content, content)

    def testServiceConnectorRemote(self):
        service = Service1(self.ctx)
        app_wrapper = FalconWrapper()
        app_wrapper.register_route(service)
        httpd = simple_server.make_server(address, port, app_wrapper.app)
        t = Thread(target=httpd.serve_forever)
        t.start()
        connector = create_service_connector(Service1, base_path_service1)
        note = connector.mynotes.detail(123)
        self.assertTrue(isinstance(note, note_mm.get_class()))
        content = connector.notes_op.read_note()
        self.assertEqual(note.content, content)
        httpd.shutdown()
        httpd.server_close()

    def testClientResourceGetCollection(self):
        coll = self.connector.account_interface.collect()
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
        # coll = self.connector.account_interface.collect(valid_params[0])
        # self.assertEqual(len(coll), 4)
        #
        # coll = self.connector.account_interface.collect(valid_params[1])
        # self.assertEqual(len(coll), 2)
        # for a in coll:
        #     self.assertEqual(a.username, 'second_account')
        #
        # coll = self.connector.account_interface.collect(valid_params[2])
        # self.assertEqual(len(coll), 1)
        # self.assertEqual(coll[0].email, 'second@email.com')
        #
        # coll = self.connector.account_interface.collect(valid_params[3])
        # self.assertEqual(len(coll), 1)
        # for a in coll:
        #     self.assertGreaterEqual(a.friends_number, 5443)

        coll = self.connector.account_interface.collect(valid_params[4])
        self.assertEqual(len(coll), 0)

        coll = self.connector.account_interface.collect(valid_params[5])
        self.assertEqual(len(coll), 0)

    def testClientResourceGetCollectionInvalidParams(self):
        illegal_params = [
            {'username': 'first_account', 'friends_number': 1234},
            {'email': 'third@email.com'},
            {'fake': '0&username=second_account&email&second@email.com'},
            'username=second_account&email&second@email.com']
        for i in range(2):
            try:
                self.connector.account_interface.collect(illegal_params[i])
            except ClientException as e:
                continue
            else:
                self.fail(f'{ClientException} is expected.')

        for i in range(2, 4):
            try:
                self.connector.account_interface.collect(illegal_params[i])
            except TypeError:
                continue
            else:
                self.fail(f'{TypeError} is be expected.')

    def testClientResourceGetDetail(self):
        detail = self.connector.account_interface.detail(1)
        self.assertTrue(isinstance(detail, Account))

    def testClientResourceAdd(self):
        res_id = self.connector.account_interface.add(accounts[1])
        self.assertEqual(res_id, 2)

    def testClientResourceUpdate(self):
        res_id = self.connector.account_interface.add(accounts[1])
        ret = self.connector.account_interface.update(res_id, accounts[1])
        self.assertTrue(ret)

    def testClientResourceDelete(self):
        ret = self.connector.account_interface.delete(0)
        self.assertTrue(ret)

    def testClientRPCArgs(self):
        self.connector.notes_op.check_args(arg1='arg1', arg2='arg2')

    def testClientRPCReturnValue(self):
        note = self.connector.notes_op.get_note(note_id=0)
        self.assertEqual(note, 'my note')

