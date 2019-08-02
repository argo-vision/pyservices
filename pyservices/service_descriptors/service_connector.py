import abc
import inspect
import json
import logging
import re
from collections import namedtuple

import requests

from pyservices.data_descriptors.entity_codecs import JSON
from pyservices.service_descriptors.interfaces import RPCInterface, RestResourceInterface
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.utilities.exceptions import ServiceException, ClientException

logger = logging.getLogger(__package__)


class RemoteRestRequestCall:
    def __init__(self, iface_location):
        self.iface_location = iface_location

    def path(self, **kwargs):
        p = kwargs.get('path')
        if p is None:
            return self.iface_location
        else:
            return "{}/{}".format(self.iface_location, p)

    def put(self, **kwargs):
        try:
            resp = requests.put(self.path(**kwargs), data=kwargs.get('remote_data'), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        self._check_message_status(resp)
        return resp.headers['location'].split('/')[-1]

    def delete(self, **kwargs):
        try:
            resp = requests.delete(self.path(**kwargs), data=kwargs.get('remote_data'), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        self._check_message_status(resp)
        return resp.content

    def post(self, **kwargs):
        try:
            # FIXME: this is really bad
            resp = requests.post(self.path(**kwargs), json=json.loads(JSON.encode(kwargs.get('remote_data'))), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        self._check_message_status(resp)
        return resp.content

    def get(self, **kwargs):
        try:
            resp = requests.get(self.path(**kwargs), params=kwargs.get('remote_data'), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        self._check_message_status(resp)
        return resp.content

    def _check_message_status(self, resp):
        if resp is not None and resp.status_code == 403:
            raise ClientException('Forbidden request')
        if resp is None:
            raise ClientException("Response is empty")
        if not str(resp.status_code).startswith('2'):
            raise ClientException("Not a 2xx")


def local_request_call(interface, actual_method_name, local_data=None, **kwargs):
    try:
        method = getattr(interface, actual_method_name)
        data = method(**local_data)
    except Exception:
        # TODO
        raise Exception
    return data


def create_service_connector(service, service_location: str):
    """ A remote client proxy.
        Args:
            service: The class which describes the Service.
            service_location (str): The service path. (E.g.
                protocol://address:port/service_name).
                Can be "local"
        """
    if not issubclass(service, Service):
        raise ServiceException(f'The service class is not a sublcass of  {Service} ')

    interfaces_endpoints = {}

    for iface in service.interfaces():
        if issubclass(iface, RestResourceInterface):
            endpoint = RestResourceEndPoint(iface, service_location)
        elif issubclass(iface, RPCInterface):
            endpoint = RPCEndPoint(iface, service_location)
        else:
            raise NotImplementedError

        iface_name = iface._get_endpoint_name()
        if iface_name in interfaces_endpoints:
            interfaces_endpoints[iface_name.replace('-', '_')]._merge_endpoints(endpoint)
        else:
            interfaces_endpoints[iface_name.replace('-', '_')] = endpoint

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
            pass
            # self._request_conrext_manager = local_request_call
            # self._iface_location = service_location
        else:
            iface_location = f'{service_location}/{iface._get_endpoint_name()}'
            self._request_context_manager = RemoteRestRequestCall(iface_location)


class RPCEndPoint(EndPoint):
    """
    """

    def _request(self, http_method, method_name, actual_method_name):

        def RPC_request(**kwargs):
            remote_data = JSON.encode(kwargs)
            # TODO A check could be made if kwargs matches the call
            resp = http_method(
                actual_method_name=actual_method_name,
                path=method_name,
                remote_data=kwargs,
                local_data=kwargs)
            if resp and isinstance(resp, bytes):
                # comes from remote
                return json.loads(resp)
            else:
                # comes from local
                return resp

        return RPC_request

    def __init__(self, iface, service_location):
        super().__init__(iface, service_location)
        calls = iface.get_call_descriptors()
        for rpc in calls.values():
            name = rpc.path.replace('-', '_')
            if rpc.method == 'post':
                call = self._request_context_manager.post
            else:
                call = self._request_context_manager.get
            method = self._request(call, method_name=rpc.path,
                                   actual_method_name=name)
            setattr(self, name, method)


class RestResourceEndPoint(EndPoint):
    """ Represent the object used to perform actual REST calls on a given
        resource.
    """

    def __init__(self, iface, service_location):
        """ Initialize the rest resource end point.
        """
        super().__init__(iface, service_location)
        self.meta_model = iface.meta_model

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

        resp = self._request_context_manager.get(
            actual_method_name='collect', remote_data=params,
            local_data=params)
        if self._check_instances(resp, self.meta_model.get_class()):
            return resp
        return JSON.decode(resp, self.meta_model)

    def detail(self, res_id):
        # FIXME: this should be a primary key for the model, NOT DICT!
        if isinstance(res_id, dict):
            res_id = '/'.join(res_id.values())

        resp = self._request_context_manager.get(
            actual_method_name='detail', local_data={'res_id': res_id},
            path=str(res_id))
        if self._check_instances(resp, self.meta_model.get_class()):
            return resp
        return JSON.decode(resp, self.meta_model)

    def add(self, resource):
        if not self._check_instances(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))
        return self._request_context_manager.put(
            actual_method_name='add',
            remote_data=JSON.encode(
                resource),
            local_data=resource)

    def delete(self, res_id):
        # FIXME: this should be a primary key for the model, NOT DICT!
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        self._request_context_manager.delete(
            actual_method_name='delete', local_data=res_id,
            path=str(res_id))
        return True

    def update(self, res_id, resource):
        if not isinstance(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))
        # FIXME: res_id should be a primary key for the model, NOT DICT!
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        self._request_context_manager.post(
            actual_method_name='update',
            path=str(res_id),
            remote_data=resource,
            local_data={
                'res_id': res_id,
                'resource': resource})
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
