import pyservices as ps

@ps.model(id_field = None)
class Note(ps.Model):
    def __init__(self, title, content):
        self.title = title
        self.content = content


# NOTE: Path is implicitly /<prefix>. The prefix is the model class name lowered.
@ps.rest(model = Note, path = "/note")
class NoteService(ps.Service):
    def __init__(self):
        self.notes = {}

    # NOTE: The following decorator is implicit with the "get_<prefix>" method name.
    # NOTE: Also the json encoder is implicit if not specified.
    # NOTE: The <prefix>_id parameter must be defined on get/delete operations.
    @ps.get(produces = ps.JSON)
    def get_note(self, note_id):
        # NOTE: Missing value must return None, generating automagically a 404.
        return self.content.get(note_id)

    # NOTE: The <prefix> parameter must be defined on put/post operations.
    def put_note(self, note: Note):
        self.content[note.id] = note


# Generating the RESTful interface with the configured framework:
note_gateway = ps.rest_server(NoteService, {'framework': ps.frameworks.FALCON})
note_client = ps.rest_client(NoteService)

