import os

import abc
import itertools
from functools import wraps
from collections import defaultdict
import threading
from typing import NamedTuple

import falcon

import pyservices as ps
from pyservices.context import Context
import pyservices.context.microservice_utils as config_utils
from pyservices.service_descriptors.comunication_utils import HTTPRequest, \
    HTTPResponse, get_data_from_request, get_updated_response
from pyservices.service_descriptors.interfaces import HTTPInterface, \
    InterfaceOperationDescriptor, HTTPExposition

COMPONENT_DEPENDENCIES = []
COMPONENT_KEY = __name__


# REST Framework
FALCON = 'falcon'


# FIXME document, rename as App in Wrapper?
# FIXME Falcon generators can be generalized -> interfaces must provide COMMON CLASS FOR CALLSname

# Thread-local allowing request-info access:
request_info = threading.local()


class RequestInfo(NamedTuple):
    user_agent: str


class WSGIAppWrapper(abc.ABC):
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

    @staticmethod
    def get_exposed_operations(iface):
        return [x
                for x in iface._get_http_operations()
                if WSGIAppWrapper.must_expose(x)]

    @staticmethod
    def must_expose(op):
        # TODO #38
        env = os.getenv('ENVIRONMENT')
        deps = config_utils.current_dependent_remote_components()
        expose_on_deps = deps and op.exposition != HTTPExposition.FORBIDDEN
        if env == 'DEVELOPMENT' or op.exposition == HTTPExposition.MANDATORY \
                or expose_on_deps:
            return True
        # HTTPExposition.FORBIDDEN or there are not services which need this:
        return False


class FalconWrapper(WSGIAppWrapper):

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
        for iface in WSGIAppWrapper._get_interfaces(service):
            self._update_resources(iface)

    def _update_resources(self, iface: HTTPInterface):
        # Update resources from interface
        operations = defaultdict(list)

        # Aggregate calls by paths
        for op in self.get_exposed_operations(iface):
            ps.log.debug("Creating {} - {}".format(op.path, op.http_method))  # FIXME move me
            operations[op.path].append(op)

        # Update single resource for path
        for path, ops in operations.items():
            self._update_resource(path, ops)

    def _update_resource(self, path: str, operations: list):
        # Update/create single resource for given path
        resource_class_name = f'FalconResource@{path}'
        falcon_resource_dict = {f'on_{op.http_method}':
                                FalconWrapper.http_operation_wrapper(op)
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
                        # Exposing some info:
                        request_info.info = RequestInfo(
                            user_agent=req.get_header('user-agent')
                        )

                        # Executing the call:
                        data = get_data_from_request(call, HTTPRequest(req.stream.read(), req.params), **kwargs)
                        body = call.method(**data)

                        # Not processing anymore:
                        request_info.info = None

                        # Preparing the response:
                        updated_res: HTTPResponse = get_updated_response(call, body)
                        res.body = updated_res.body

                    except Exception as e:  # TODO be more precise, exception translations #23
                        ps.log.debug(e)
                        res.status = falcon.HTTP_500

                return falcon_handler


def register_component(ctx: Context):
    app = FalconWrapper()  # TODO falcon is the only WSGI app supported
    ctx.register_app(app)  # TODO think about register_app (get_app)
