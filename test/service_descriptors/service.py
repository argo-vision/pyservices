from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RPC, \
    RestResourceInterface, RPCInterface
from pyservices.data_descriptors.entity_codecs import JSON
from test.data_descriptors.meta_models import *


class AccountManager(Service):
    service_base_path = 'account-manager'
    if_path = 'notes'  # NOTE: shared with RPC

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

    class NotesOperations(RPCInterface):
        if_path = 'notes-op'  # NOTE: shared with REST

        def __init__(self, service):
            super().__init__(service)
            self.arg1 = 'arg1'
            self.arg2 = 'arg2'
            self.notes = ['my note']

        def check_args(self, arg1, arg2):
            assert(arg1 == self.arg1)
            assert(arg2 == self.arg2)

        def get_note(self, note_id):
            return self.notes[note_id]


    class Note(RestResourceInterface):
        meta_model = NoteMM

        def collect(self):
            return notes
