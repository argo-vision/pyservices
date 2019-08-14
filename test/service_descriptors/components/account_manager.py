from pyservices.context import Context
from pyservices.service_descriptors.interfaces import RPC, \
    RestResourceInterface, RPCInterface
from pyservices.service_descriptors.layer_supertypes import Service
from test.data_descriptors.meta_models import *

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper']
COMPONENT_KEY = __name__


class AccountManager(Service):
    service_base_path = 'account-manager'
    if_path = 'notes'  # NOTE: shared with RPC

    class NotesOperations(RPCInterface):
        if_path = 'notes-op'  # NOTE: shared with REST

        def __init__(self, service):
            super().__init__(service)
            self.arg1 = 'arg1'
            self.arg2 = 'arg2'
            self.notes = ['my note']

        @RPC(method="get")
        def check_args(self, arg1, arg2):
            assert(arg1 == self.arg1)
            assert(arg2 == self.arg2)

        @RPC(method="post")
        def no_args(self):
            assert True

        def get_note(self, note_id):
            return self.notes[note_id]

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

        def add(self, resource):
            res_id = '123'
            assert isinstance(resource, (Account, list))
            return res_id

        def update(self, res_id, resource):
            assert type(res_id) is int
            assert type(resource) is Account

        def delete(self, res_id):
            assert type(res_id) is int

    class Note(RestResourceInterface):
        meta_model = NoteMM

        def collect(self):
            return notes


def register_component(ctx: Context):
    service = AccountManager()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)
