import abc
import collections
import inspect
import itertools
import json
import logging
from functools import wraps
from json.decoder import JSONDecodeError
from collections import defaultdict

import falcon

import pyservices as ps
from pyservices.context import Context
from pyservices.data_descriptors import entity_codecs
from pyservices.data_descriptors.fields import ComposedField
from pyservices.service_descriptors.interfaces import RestResourceInterface, \
    RPCInterface, HTTPInterface, InterfaceOperationDescriptor
from pyservices.utilities.exceptions import HTTPNotFound

COMPONENT_DEPENDENCIES = []
COMPONENT_KEY = __name__


# REST Framework
FALCON = 'falcon'


# FIXME document, rename as App in Wrapper?
# FIXME Falcon generators can be generalized -> interfaces must provide COMMON CLASS FOR CALLSname

class FrameworkApp(abc.ABC):
    """ Base class for frameworks, it is used to crete WSGI applications.
    """

    def __init__(self):
        # TODO log
        self.app = None

    # FIXME pyservices as component, register_services (not routes)
    def register_route(self, service):
        pass

    @staticmethod
    def _get_interfaces(service):
        return [iface_desc
                for iface_desc in service.interface_descriptors
                if issubclass(iface_desc.__class__, HTTPInterface)]


class FalconApp(FrameworkApp):

    def __init__(self):
        super().__init__()
        self.app = falcon.API()
        self._resources = {}

    def register_route(self, service):
        # get falcon rest resources
        self._update_falcon_resource(service)

        # register routes and resources
        for path, r in self._resources.items():
            res = r()
            self.app.add_route(path, res)

        self._log_registered_urls()

    def _log_registered_urls(self):
        # Logging registered uris
        registered_uris = [x.uri_template for x in self.app._router._roots
                           if x.uri_template is not None]
        children = itertools.chain.from_iterable(
            (x.children for x in self.app._router._roots))
        registered_uris += [x.uri_template for x in children]
        for uri in registered_uris:
            ps.log.info("Registered: {}".format(uri))

    def _update_falcon_resource(self, service):
        # Update resources for every interface of the service
        for iface in FrameworkApp._get_interfaces(service):
            self._update_resources(iface)

    def _update_resources(self, iface: HTTPInterface):
        # Update resources from interface
        operations = defaultdict(list)

        # Aggregate calls by paths
        for op in iface._get_http_operations():
            ps.log.error("Creating {} - {}".format(op.path, op.http_method))
            operations[op.path].append(op)

        # Update single resource for path
        for path, ops in operations.items():
            self._update_resource(path, ops)

    def _update_resource(self, path: str, operations: list):
        # Update/create single resource for given path
        resource_class_name = f'FalconResource@{path}'
        falcon_resource_dict = {f'on_{op.http_method}':
                                FalconApp.http_operation_wrapper(op)
                                for op in operations}
        resource = self._resources.get(path)
        if resource:
            [setattr(resource, name, method)
             for name, method in falcon_resource_dict.items()]
        else:
            self._resources[path] = \
                type(resource_class_name, (object,), falcon_resource_dict)

    @staticmethod
    def http_operation_wrapper(call: InterfaceOperationDescriptor):
                @wraps(call)
                def falcon_handler(inner_self, req, res, **kwargs):
                    try:
                        data = FalconApp._get_request_data(call, req, **kwargs)
                        body = call.method(**data)
                        FalconApp._update_response(call, res, body)

                    except Exception as e:  # TODO be more precise, exception translations #23
                        res.status = falcon.HTTP_500

                return falcon_handler

    @staticmethod
    def _get_request_data(call, req, **kwargs):
        has_meta_model = hasattr(call.interface, 'meta_model')
        ret = {}
        if kwargs:
            # The only kwargs supported are the auto-generated for single
            # resource operation, kwargs represent id
            if not has_meta_model:
                raise Exception  # TODO
            if hasattr(call.interface.meta_model, 'primary_key_field'):
                ret['res_id'] = call.interface.meta_model.validate_id(**kwargs)

        if call.encoder and call.http_method in ("put", "post"):
            # Expects some data
            data = req.stream.read()
            if data and has_meta_model:
                # Data has a specific shape
                ret['resource'] = (call.encoder.decode(
                    data, call.interface.meta_model))
            elif data:
                # Data hasn't a specific shape
                d = call.encoder.decode_unshaped(data)
                if isinstance(d, dict):
                    ret.update(d)
                else:
                    # Only dict as non shaped is supported
                    raise NotImplementedError()
        elif call.http_method == "get" and req.params:
            # Data, if present, is placed on request param
            ret.update(req.params)

        return ret

    @staticmethod
    def _update_response(call, res, body):
        if body:
            res.body = call.decoder.encode(body)


def register_component(ctx: Context):
    app = FalconApp()  # TODO falcon is the only WSGI app supported
    ctx.register_app(app)  # TODO think about register_app (get_app)
