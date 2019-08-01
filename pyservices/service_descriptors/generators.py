import logging
import re
import abc
import inspect
import json
from collections import namedtuple
from contextlib import contextmanager

import requests

from pyservices.data_descriptors.entity_codecs import Codec, JSON
from pyservices.utilities.exceptions import ServiceException, ClientException, \
    CodecException
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RPCInterface, \
    RestResourceInterface
from pyservices.utilities.exceptions import HTTPException

logger = logging.getLogger(__package__)


class ServiceConnector:
    """ A remote client proxy.

    Class attributes:
        clients (dict): Contains the client of different services, the key
            are the URI of the resource.
    """

    @staticmethod
    @contextmanager
    def requests_call(method, path, **kwargs):
        """ Wrapper used to perform requests and checks.
        """
        try:
            resp = method(path, **kwargs, timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        # TODO more status codes could be handled
        if resp is not None and resp.status_code == 403:
            raise ClientException('Forbidden request')
        if resp is None:
            raise ClientException("Response is empty")

        yield resp

    def __init__(self, service_class, service_location: str = 'local',
                 codec: Codec = None):
        """ TODO.

        Args:
            service_class: The class which describes the Service.
            service_location (str): The service path. (E.g.
                protocol://address:port/service_name, can be local).
            codec (Codec): The codec used for the communication
        """
        if not issubclass(service_class, Service):
            raise ServiceException(f'The service class is not a {Service} '
                                   f'instance.')

        interfaces = service_class.get_interfaces()

        if codec is None and [issubclass(iface, RestResourceInterface)
                              for iface in interfaces]:
            raise CodecException('A Codec for a connector of a REST interface.')

        interfaces_endpoints = {}
        for iface in interfaces:
            iface_name = iface._get_endpoint_name()
            iface_path = f'{service_location}/{iface_name}'
            if issubclass(iface, RestResourceInterface):
                endpoint = RestResourceEndPoint(iface_path, iface.meta_model,
                                                codec)
            elif issubclass(iface, RPCInterface):
                endpoint = RPCEndPoint(iface_path, iface._get_call_descriptors())
            else:
                raise NotImplementedError
            if iface_name in interfaces_endpoints:
                interfaces_endpoints[iface_name]._merge_endpoints(endpoint)
            else:
                interfaces_endpoints[iface_name] = endpoint

        for path in interfaces_endpoints.keys():
            interfaces_endpoints[path.replace('-', '_')] = \
                interfaces_endpoints.pop(path)
        interfaces_tuple = namedtuple('Interfaces', interfaces_endpoints.keys())
        self.interfaces = interfaces_tuple(**interfaces_endpoints)


class EndPoint(abc.ABC):
    def _merge_endpoints(self, *args):
        for arg in args:
            if not issubclass(type(arg), EndPoint):
                raise Exception  # FIXME too general

            methods = inspect.getmembers(arg)  # methods and attributes
            for (n, m) in methods:
                if not n.startswith('_'):
                    setattr(self, n, m)


class RPCEndPoint(EndPoint):
    """
    """

    @staticmethod
    def _request(method, path):
        def RPC_request(self, **kwargs):
            # TODO A check could be made if kwargs matches the call
            with RemoteServiceConnector.requests_call(
                    method, path, data=json.dumps(kwargs).encode('UTF-8')) \
                    as resp:
                if resp.status_code == 200:
                    body = resp.content
                    if len(body):
                        return json.loads(body)
                    else:
                        return
                raise HTTPException()
        return RPC_request

    def __init__(self, path, RPCs):
        self.path = path
        for rpc in RPCs.values():
            name = rpc.path.replace('-', '_')  # TODO move conversion? this should be done is 2 places
            method = RPCEndPoint._request(requests.post, f'{path}/{rpc.path}')
            setattr(self, name, method)


class RestResourceEndPoint(EndPoint):
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
        with RemoteServiceConnector.requests_call(
                requests.get, path=self.path, params=params) as resp:
            if resp.status_code == 200:
                data = self.codec.decode(resp.content, self.meta_model)
                return data

    def detail(self, res_id):
        # FIXME: this should be a primary key for the model
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        path = f'{self.path}/{res_id}'

        with RemoteServiceConnector.requests_call(
                requests.get, path=path) as resp:
            if resp.status_code == 200:
                data = self.codec.decode(resp.content, self.meta_model)
                return data

    def add(self, resource):
        if not self._check_instances(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))

        resource = self.codec.encode(resource)
        logger.info("Put on {}".format(self.path))
        with RemoteServiceConnector.requests_call(
                requests.put, path=self.path, data=resource) as resp:

            if resp.status_code == 201:
                loc = resp.headers['location']
                res_id = loc.replace(resp.request.path_url + '/', '')
                # FIXME: this should be maybe a primary key?
                return res_id

        raise RuntimeError("Server side exception")

    @staticmethod
    def _check_instances(resource, resource_class):
        if isinstance(resource, list):
            for res in resource:
                if not isinstance(res, resource_class):
                    return False
            return True
        else:
            return isinstance(resource, resource_class)

    def delete(self, res_id):
        # FIXME: res_id should be a primary key for the model
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        path = f'{self.path}/{res_id}'

        with RemoteServiceConnector.requests_call(
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
        with RemoteServiceConnector.requests_call(
                requests.post, path=path, data=resource) as resp:
            if resp.status_code == 200:
                return True


class RestGenerator:

    @classmethod
    def get_client_proxy(cls, service_address: str, service_port: str,
                         service_class, codec: Codec = JSON) -> RemoteServiceConnector:
        """ Method used to generate a REST client.
        """
        service_path = f'http://{service_address}:{service_port}/' \
            f'{service_class.service_base_path}'
        client = RemoteServiceConnector(service_path, service_class, codec)
        return client
