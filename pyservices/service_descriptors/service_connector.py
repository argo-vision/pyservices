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

logger = logging.getLogger(__package__)


@contextmanager
def remote_request_call(http_method, path, remote_data=None, **kwargs):
    """ Wrapper used to perform requests and checks. TODO
    """
    try:
        resp = http_method(path, data=remote_data, timeout=5)
    except Exception:
        raise ClientException('Exception on request')

    # TODO more status codes could be handled
    if resp is not None and resp.status_code == 403:
        raise ClientException('Forbidden request')
    if resp is None:
        raise ClientException("Response is empty")
    yield resp.content


@contextmanager
def local_request_call(interface, actual_method_name, local_data=None,
                       **kwargs):
    try:
        method = getattr(interface, actual_method_name)
        data = method(**local_data)
    except Exception:
        # TODO
        raise Exception
    yield data


def create_service_connector(service, service_location: str, codec=JSON):
    """ A remote client proxy.
        Args:
            service: The class which describes the Service.
            service_location (str): The service path. (E.g.
                protocol://address:port/service_name).
                Can be "local"
            codec (Codec): The codec used for the communication
        """
    if not isinstance(service, Service):
        raise ServiceException(f'The service class is not a {Service} '
                               f'instance.')

    if codec is None and [issubclass(iface, RestResourceInterface)
                          for iface in service.interface_descriptors]:
        raise CodecException('A Codec for a connector of a REST interface.')

    interfaces_endpoints = {}
    for iface in service.interface_descriptors:
        iface_name = iface._get_endpoint_name()
        if isinstance(iface, RestResourceInterface):
            endpoint = RestResourceEndPoint(iface, service_location, codec)
        elif isinstance(iface, RPCInterface):
            endpoint = RPCEndPoint(iface, service_location)
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
    return interfaces_tuple(**interfaces_endpoints)


class EndPoint(abc.ABC):
    def _merge_endpoints(self, *args):
        for arg in args:
            if not issubclass(type(arg), EndPoint):
                raise Exception  # FIXME too general

            methods = inspect.getmembers(arg)  # methods and attributes
            for (n, m) in methods:
                if not n.startswith('_'):
                    setattr(self, n, m)

    def __init__(self, iface, service_location):
        """ Initialize the end point.
        """
        if service_location == 'local':
            self._request_context_manager = local_request_call
            self._iface_location = service_location
        else:
            self._request_context_manager = remote_request_call
            self._iface_location = f'{service_location}/{iface._get_endpoint_name()}'
        self._iface = iface


class RPCEndPoint(EndPoint):
    """
    """

    def _request(self, http_method, method_name, actual_method_name):
        path = f'{self._iface_location}/{method_name}'

        def RPC_request(**kwargs):
            # TODO A check could be made if kwargs matches the call
            with self._request_context_manager(
                    http_method=http_method,
                    interface=self._iface,
                    actual_method_name=actual_method_name,
                    path=path,
                    remote_data=json.dumps(kwargs).encode('UTF-8'),
                    local_data=kwargs) as resp:
                if resp and isinstance(resp, bytes):
                    # comes from remote
                    return json.loads(resp)
                else:
                    # comes from local
                    return resp

        return RPC_request

    def __init__(self, iface, service_location):
        super().__init__(iface, service_location)
        calls = iface._get_call_descriptors()
        for rpc in calls.values():
            name = rpc.path.replace('-', '_')
            method = self._request(requests.post, method_name=rpc.path,
                                   actual_method_name=name)
            setattr(self, name, method)


class RestResourceEndPoint(EndPoint):
    """ Represent the object used to perform actual REST calls on a given
        resource.
    """

    def __init__(self, iface, service_location, codec):
        """ Initialize the rest resource end point.
        """
        super().__init__(iface, service_location)
        self.meta_model = iface.meta_model
        self.codec = codec

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

        with self._request_context_manager(
                http_method=requests.get, interface=self._iface,
                actual_method_name='collect', remote_data=params,
                local_data=params, path=self._iface_location) as resp:
            if self._check_instances(resp, self.meta_model.get_class()):
                return resp
            return self.codec.decode(resp, self.meta_model)

    def detail(self, res_id):
        # FIXME: this should be a primary key for the model, NOT DICT!
        if isinstance(res_id, dict):
            res_id = '/'.join(res_id.values())

        path = f'{self._iface_location}/{res_id}'
        with self._request_context_manager(
                http_method=requests.get, interface=self._iface,
                actual_method_name='detail', local_data={'res_id': res_id},
                path=path) as resp:
            if self._check_instances(resp, self.meta_model.get_class()):
                return resp
            return self.codec.decode(resp, self.meta_model)

    def add(self, resource):
        if not self._check_instances(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))
        logger.info("Put on {}".format(self._iface_location))
        with self._request_context_manager(http_method=requests.put,
                                          interface=self._iface,
                                          actual_method_name='add',
                                          path=self._iface_location,
                                          remote_data=self.codec.encode(
                                              resource),
                                          local_data=resource) \
                as resp:
            return resp

    def delete(self, res_id):
        # FIXME: this should be a primary key for the model, NOT DICT!
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        path = f'{self._iface_location}/{res_id}'
        with self._request_context_manager(
                http_method=requests.delete, interface=self._iface,
                actual_method_name='delete', local_data=res_id,
                path=path) as resp:
            return True

    def update(self, res_id, resource):
        if not isinstance(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))
        # FIXME: res_id should be a primary key for the model, NOT DICT!
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())
        resource = self.codec.encode(resource)
        path = f'{self._iface_location}/{res_id}'
        with self._request_context_manager(http_method=requests.post,
                                          interface=self._iface,
                                          actual_method_name='update',
                                          path=path,
                                          remote_data=self.codec.encode(
                                              resource),
                                          local_data={
                                              'res_id': res_id,
                                              'resource': resource}) \
                as resp:
            return True

    @staticmethod
    def _check_instances(resource, resource_class):
        if isinstance(resource, list):
            for res in resource:
                if not isinstance(res, resource_class):
                    return False
            return True
        else:
            return isinstance(resource, resource_class)