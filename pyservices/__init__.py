# This is the module facade, importing classes from the src dir/module.
# TODO
import logging

# from .decorators import rest_add, rest_collection, rest_delete, \
#     rest_detail, rest_update
from .entity_codecs import JSON, Codec
from . import http_content_types, frameworks
from .interfaces import RestResource
from .generators import RestGenerator

log = logging.getLogger(__package__)
name = 'pyservices'
