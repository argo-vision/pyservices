# This is the module facade, importing classes from the src dir/module.
import logging

# from .decorators import rest_add, rest_collection, rest_delete, \
#     rest_detail, rest_update
from pyservices.data_descriptors.entity_codecs import JSON
from pyservices.service_descriptors import WSGIAppWrapper, http_content_types

log = logging.getLogger(__package__)
name = 'pyservices'
