# This is the module facade, importing classes from the src dir/module.
# TODO
import logging

# from .decorators import rest_add, rest_collection, rest_delete, \
#     rest_detail, rest_update
from pyservices.data_descriptors.entity_codecs import JSON, Codec
from pyservices.service_descriptors import frameworks, http_content_types

log = logging.getLogger(__package__)
name = 'pyservices'
