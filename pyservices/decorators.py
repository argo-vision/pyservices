from .entity_codecs import JSON, Codec


# Mapping between rest and HTTP methods:
#   GET         /user           query
#   PUT         /user           creo
#   GET         /user/id        ottengo
#   POST        /user/id        update
#   DELETE      /user/id        cancello


def rest(model, path=None):
    pass


def get(produces=None):
    if produces and not isinstance(produces, Codec):
        raise TypeError('Expected {}, found {}'.format(Codec, type(produces)))

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
    if produces and not isinstance(produces, Codec):
        raise TypeError('Expected {}, found {}'.format(Codec, type(produces)))

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
    if consumes and not isinstance(consumes, Codec):
        raise TypeError('Expected {}, found {}'.format(Codec, type(consumes)))

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
    if consumes and not isinstance(consumes, Codec):
        raise TypeError('Expected {}, found {}'.format(Codec, type(consumes)))

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


