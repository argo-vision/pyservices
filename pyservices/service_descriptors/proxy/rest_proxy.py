import json
import re
from abc import abstractmethod

import requests

from pyservices import JSON
from pyservices.service_descriptors.proxy.proxy_interface import EndPoint
from pyservices.utilities.exceptions import ClientException


def _check_instances(resource, resource_class):
    if isinstance(resource, list):
        for res in resource:
            if not isinstance(res, resource_class):
                return False
        return True
    else:
        return isinstance(resource, resource_class)


def _check_message_status(resp):
    if resp is not None and resp.status_code == 403:
        raise ClientException('Forbidden request')
    if resp is None:
        raise ClientException("Response is empty")
    if not str(resp.status_code).startswith('2'):
        raise ClientException("Not a 2xx")


class RestEndPoint(EndPoint):
    @abstractmethod
    def add(self, data):
        pass

    @abstractmethod
    def delete(self, res_id):
        pass

    @abstractmethod
    def update(self, res_id, data):
        pass

    @abstractmethod
    def collect(self, data):
        pass

    @abstractmethod
    def detail(self, res_id):
        pass


class RemoteRestRequestCall(RestEndPoint):
    def __init__(self, iface_location, meta_model):
        self.iface_location = iface_location
        self.model = meta_model

    def path(self, path):
        if path is None:
            return self.iface_location
        else:
            return "{}/{}".format(self.iface_location, path)

    def add(self, data):
        if not _check_instances(data, self.model.get_class()):
            raise ValueError('Expected a {}'.format(self.model.name))
        try:
            resp = requests.put(self.path(None), data=JSON.encode(data), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        _check_message_status(resp)
        return resp.headers['location'].split('/')[-1]

    def delete(self, res_id):
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        try:
            resp = requests.delete(self.path(res_id), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        _check_message_status(resp)
        return resp.content

    def update(self, res_id, data):
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        try:
            # FIXME: this use of json is really bad
            resp = requests.post(self.path(res_id), json=json.loads(JSON.encode(data)), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        _check_message_status(resp)
        return resp.content

    def collect(self, data):
        try:
            resp = requests.get(self.path(None), params=data, timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        _check_message_status(resp)
        return JSON.decode(resp.content, self.model)

    def detail(self, res_id):
        if isinstance(res_id, dict):
            res_id = '/'.join(res_id.values())
        try:
            resp = requests.get(self.path(res_id), timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        _check_message_status(resp)
        return JSON.decode(resp.content, self.model)


class RestEndPointDispatcher(RestEndPoint):
    """ Represent the object used to perform actual REST calls on a given
        resource.
    """

    def __init__(self, iface, service_location):
        """ Initialize the rest resource end point.
        """
        if service_location == 'local':
            pass
            # self._request_conrext_manager = local_request_call
            # self._iface_location = service_location
        else:
            iface_location = f'{service_location}/{iface.get_endpoint_name()}'
            self._request_handler = RemoteRestRequestCall(iface_location, iface.meta_model)
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

        return self._request_handler.collect(params)

    def detail(self, res_id):
        # FIXME: this should be a primary key for the model, NOT DICT!

        return self._request_handler.detail(res_id)

    def add(self, resource):
        return self._request_handler.add(resource)

    def delete(self, res_id):
        # FIXME: this should be a primary key for the model, NOT DICT!
        self._request_handler.delete(res_id)
        return True

    def update(self, res_id, resource):
        if not isinstance(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))

        self._request_handler.update(res_id, resource)
        return True
