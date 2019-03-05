import functools

from .entity_codecs import JSON, Codec


# Mapping between rest and HTTP methods:
#   GET         /user           query
#   PUT         /user           creo
#   GET         /user/id        ottengo
#   POST        /user/id        update
#   DELETE      /user/id        cancello


# TODO NOT ENOUGHT DRY
# TODO this decorators are related to a particolar type of interface (the REST one). They could be better organized (decorator/class)
def rest_detail(meta_model, produces=None, uri=None):
    if produces and not issubclass(produces, Codec):
        raise TypeError(f'Expected {Codec}, found {type(produces)}')
    if not uri:
        uri = meta_model.name + 's'
    uri = uri.lower()

    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'operation': 'detail',
            'produces': produces or JSON,
            'uri': uri,
            'resource_meta_model': meta_model
        }

        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def rest_collection(meta_model, produces=None, uri=None):
    if produces and not issubclass(produces, Codec):
        raise TypeError(f'Expected {Codec}, found {type(produces)}')
    if not uri:
        uri = meta_model.name + 's'
    uri = uri.lower()

    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'operation': 'list',
            'produces': produces or JSON,
            'resource_meta_model': meta_model,
            'uri': uri
        }

        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def rest_add(meta_model, consumes=None, uri=None):
    if consumes and not issubclass(consumes, Codec):
        raise TypeError(f'Expected {Codec}, found {type(consumes)}')

    if not uri:
        uri = meta_model.name + 's'
    uri = uri.lower()

    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'operation': 'add',
            'consumes': consumes or JSON,
            'uri': uri,
            'resource_meta_model': meta_model,
        }

        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def rest_update(meta_model, consumes=None, uri=None):
    if consumes and not issubclass(consumes, Codec):
        raise TypeError(f'Expected {Codec}, found {type(consumes)}')

    if not uri:
        uri = meta_model.name + 's'
    uri = uri.lower()

    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'operation': 'update',
            'consumes': consumes or JSON,
            'uri': uri,
            'resource_meta_model': meta_model,
        }
        
        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


def rest_delete(meta_model, uri=None):
    if not uri:
        uri = meta_model.name + 's'
    uri = uri.lower()

    def dec(fn):
        # Appending some info:
        fn.rest_interface = {
            'operation': 'delete',
            'uri': uri,
            'resource_meta_model': meta_model,
        }
        
        # Not changing the original function:
        return fn

    # The decorator instance:
    return dec


