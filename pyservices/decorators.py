from .entity_codecs import JSON


# Mapping between rest and HTTP methods:
#   GET         /user           query
#   PUT         /user           creo
#   GET         /user/id        ottengo
#   POST        /user/id        update
#   DELETE      /user/id        cancello


def rest(model, path=None):
    pass


# TODO following decorators should check for Codec type (type(produces|consumes) == Codec)
def get(produces=None):
    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'method': 'GET',
            'produces': produces or JSON,
            'path': r'/\w+'
        }

        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def get_list(produces=None):
    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'method': 'GET',
            'produces': produces or JSON,
            'path': r''  # TODO: add query, order and res numb support
        }

        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def put(consumes=None):
    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'method': 'PUT',
            'consumes': consumes or JSON,
            'path': r''
        }

        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def post(consumes=None):
    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'method': 'POST',
            'consumes': consumes or JSON,
            'path': '/\w+'
        }
        
        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def delete():
    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'method': 'DELETE',
            'path': r'/\w+'

        }
        
        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


