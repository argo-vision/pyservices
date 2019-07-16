import hashlib
import itertools
import logging
import re
from collections import namedtuple
from contextlib import contextmanager
from threading import Thread
from wsgiref import simple_server

import falcon
import requests

import pyservices as ps
from pyservices.data_descriptors.entity_codecs import Codec, JSON, \
    instance_to_dict_repr
from pyservices.exceptions import ServiceException, ClientException
from pyservices.service_descriptors.frameworks import FALCON
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import HTTPInterface, RPCInterface, RestResourceInterface

logger = logging.getLogger(__package__)


class HTTPClient:
    """ A client proxy.

    Class attributes:
        clients (dict): Contains the client of different services, the key
            are the URI of the resource.
    """

    @staticmethod
    @contextmanager
    def requests_call(method, path, **kwargs):
        """ Wrapper used to perform requests and checks.

        """
        resp = None
        try:
            resp = method(path, **kwargs, timeout=5)
            yield resp
        except Exception:
            raise ClientException('Exception on request')

        finally:
            # TODO more status codes could be handled
            if resp is not None and resp.status_code == 403:
                raise ClientException('Forbidden request')
            if resp is None:
                raise ClientException("Response is empty")

    # TODO move codec elsewhere (it is a dependency of data-related ifaces? Otherwise throw exception
    def __init__(self, service_path: str, service_class, codec: Codec):
        """ Initialize a REST client proxy.

        Args:
             service_path (str): The service path. (E.g.
                protocol://address:port/service_name)
            service_class: The class which describes the Service.
            codec (Codec): The codec used for the communication # TODO it's likely that this will be moved in the dependencies
        """
        if not issubclass(service_class, Service):
            raise ServiceException(f'The service class is not a {Service} '
                                   f'instance.')
        service_path = service_path

        ifaces = service_class.get_interfaces()
        ifaces_endpoints = {'REST': {}, 'RPC': {}}
        # TODO generalizable
        for iface in ifaces:
            iface_name = iface._get_endpoint_name()
            iface_path = f'{service_path}/{iface_name}'
            if issubclass(iface, RestResourceInterface):
                ifaces_endpoints['REST'][iface_name] = RestResourceEndPoint(
                    iface_path, iface.meta_model, codec)
            elif issubclass(iface, RPCInterface):
                ifaces_endpoints['RPC'][iface_name] = RPCEndPoint(
                    iface_path, iface._get_RPCs())

        for iface_type, v in ifaces_endpoints.items():
            # TODO this conversion could come handy in other places
            for key in v.keys():
                if key.count('-'):
                    v[key.replace('-', '_')] = v.pop(key)
            interfaces_tuple = namedtuple(iface_type, v.keys())
            ifaces_endpoints[iface_type] = interfaces_tuple(**v)
        interfaces_tuple = namedtuple('Interfaces', ifaces_endpoints.keys())
        self.interfaces = interfaces_tuple(**ifaces_endpoints)


class RPCEndPoint:
    """
    """

    @classmethod
    def _request(cls, method, path):
        def RPC_request(**kwargs):
            # TODO do some checks on kwargs
            with HTTPClient.requests_call(method, path, **kwargs):
                return True
            return False
        return RPC_request

    def __init__(self, path, RPCs):
        self.path = path
        for rpc in RPCs:
            name = rpc.path.replace('-', '_')  # TODO move conversion?
            fun = RPCEndPoint._request(
                getattr(requests, rpc.http_method),
                f'{path}/{name}')
            setattr(self, name, fun)


class RestResourceEndPoint:
    """ Represent the object used to perform actual REST calls on a given
        resource.
    """

    def __init__(self, path, meta_model, codec):
        """ Initialize the end point.
        """
        self.path = path
        self.codec = codec
        self.meta_model = meta_model

    def collect(self, params: dict = None):
        if params:
            if not isinstance(params, dict):
                raise TypeError(
                    f'The type of params must be a dict. Not a {type(params)}')
            illegal_params_re = re.compile('[&=#]')
            for k, v in params.items():
                if not isinstance(k, str):
                    raise TypeError(f'The param keys must be strings.')
                if illegal_params_re.search(k):
                    raise TypeError(f'The param keys cannot contain '
                                    f'{illegal_params_re.pattern}.')
                if isinstance(v, str) and illegal_params_re.search(v):
                    raise TypeError(f'The param values cannot contain '
                                    f'{illegal_params_re.pattern}.')
        with HTTPClient.requests_call(
                requests.get, path=self.path, params=params) as resp:
            if resp.status_code == 200:
                data = self.codec.decode(resp.content, self.meta_model)
                return data

    def detail(self, res_id):
        # FIXME: this should be a primary key for the model
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        path = f'{self.path}/{res_id}'

        with HTTPClient.requests_call(
                requests.get, path=path) as resp:
            if resp.status_code == 200:
                data = self.codec.decode(resp.content, self.meta_model)
                return data

    def add(self, resource):
        if not isinstance(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))
        resource = self.codec.encode(resource)
        # resource = instance_to_dict_repr(resource)  # TODO temporary
        with HTTPClient.requests_call(
                requests.put, path=self.path, data=resource) as resp:

            if resp.status_code == 201:
                loc = resp.headers['location']
                res_id = loc.replace(resp.request.path_url + '/', '')
                # FIXME: this should be maybe a primary key?
                return res_id

        raise RuntimeError("Server side exception")

    def delete(self, res_id):
        # FIXME: res_id should be a primary key for the model
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        path = f'{self.path}/{res_id}'

        with HTTPClient.requests_call(
                requests.get, path=path) as resp:
            if resp.status_code == 200:
                return True

    def update(self, res_id, resource):
        # FIXME: res_id should be a primary key for the model
        if not isinstance(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))

        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())
        resource = self.codec.encode(resource)
        path = f'{self.path}/{res_id}'
        with HTTPClient.requests_call(
                requests.post, path=path, data=resource) as resp:
            if resp.status_code == 200:
                return True


class RestGenerator:
    """ Class used to generate the rest server and client.
    """

    @classmethod
    def get_client_proxy(cls, service_address: str, service_port: str,
                         service_base_path: str, service_class,
                         codec: Codec = JSON) -> HTTPClient:
        """ Method used to generate a REST client.
        """
        service_path = f'http://{service_address}:{service_port}/' \
            f'{service_base_path}'
        client = HTTPClient(service_path, service_class, codec)
        return client
