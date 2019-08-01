from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RestResourceInterface, \
    RPCInterface

from pyservices.data_descriptors.meta_model import MetaModel
from pyservices.data_descriptors.fields import StringField

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks']
COMPONENT_KEY = __name__

note_mm = MetaModel('Note', StringField('title'), StringField('content'),
                    primary_key_name='title')

my_notes = [note_mm.get_class()('My title', 'My content')]


class Service1(Service):
    service_base_path = 'Service1'

    class NoteRestResourceInterface(RestResourceInterface):
        meta_model = note_mm

        def detail(self, res_id):
            return my_notes[0]

    class NotesOperation(RPCInterface):
        if_path = 'notes-op'

        def read_note(self):
            return my_notes[0].content


def register_component(ctx: Context):
    service = Service1()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)
