from .entity_codecs import JSON


# Mapping between rest and HTTP methods:
#   GET         /user           query
#   PUT         /user           creo
#   GET         /user/id        ottengo
#   POST        /user/id        update
#   DELETE      /user/id        cancello


def rest(model, path=None):
    pass


def get(produce=None):
    pass


def get_list(produces=None):
    pass


def put(consumes=None):
    pass


def post(consumes=None):
    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'method': 'POST',
            'consumes': consumes or JSON
        }
        
        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def delete():
    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'method': 'DELETE'
        }
        
        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


