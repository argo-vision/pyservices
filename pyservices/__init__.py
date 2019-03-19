# This is the module facade, importing classes from the src dir/module.
# TODO
import logging
import logging.config


from .decorators import rest_add, rest_collection, rest_delete, \
    rest_detail, rest_update
from .entity_codecs import JSON, Codec
from .layer_supertypes import Model, Service
from . import http_content_types, frameworks
from .interfaces import RestfulResource

LOGGER_NAME = 'pyservices'

# TODO move this
logger_config = {
    'version': 1,
    'formatters': {
        'baseFormatter': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}},
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'baseFormatter',
            'stream': 'ext://sys.stdout',
            'level': 'DEBUG'}},
    'loggers': {
        'pyservices': {
            'level': 'DEBUG'}}}
logging.config.dictConfig(logger_config)
logging.debug('Logger configuration loaded.')

name = 'pyservices'
