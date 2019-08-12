import json

import requests

from pyservices.service_descriptors.proxy.proxy_interface import EndPoint
from pyservices.utils.exceptions import ClientException


class RemoteRPCRequestCall:
    def __init__(self, iface_location):
        self.iface_location = iface_location

    def path(self, path=None):
        if path is None:
            return self.iface_location
        else:
            return "{}/{}".format(self.iface_location, path)

    def post(self, path, data):
        try:
            # FIXME: this is really bad
            resp = requests.post(self.path(path), json=data, timeout=5)
        except Exception as e:
            raise ClientException('Exception on post request to'.format(path))

        self._check_message_status(resp)
        return json.loads(resp.content) if resp.content else None

    def get(self, path, data):
        try:
            resp = requests.get(self.path(path), params=data, timeout=5)
        except Exception as e:
            raise ClientException('Exception on get request to {}'.format(path))

        self._check_message_status(resp)
        return json.loads(resp.content) if resp.content else None

    def _check_message_status(self, resp):
        if resp is not None and resp.status_code == 403:
            raise ClientException('Forbidden request')
        if resp is None:
            raise ClientException("Response is empty")
        if not str(resp.status_code).startswith('2'):
            raise ClientException("Not a 2xx")


class LocalRPCRequestCall:
    def __init__(self, iface_instance):
        self.instance = iface_instance

    def call(self, method, data):
        try:
            m = getattr(self.instance, method)
            data = m(**data)
        except Exception:
            # TODO
            raise Exception
        return data


class RPCDispatcherEndPoint(EndPoint):
    def _request(self, http_method, method_name):

        def RPC_request(**kwargs):
            # TODO A check could be made if kwargs matches the call
            return http_method(method_name, kwargs)

        return RPC_request

    def __init__(self, iface, service_location):
        if type(service_location) == str:
            iface_location = f'{service_location}/{iface._get_interface_path()}'
            self._request_handler = RemoteRPCRequestCall(iface_location)
            calls = iface._get_class_calls()
            for rpc in calls.values():
                name = rpc.path.replace('-', '_')
                if rpc.http_method == 'post':
                    call = self._request_handler.post
                else:
                    call = self._request_handler.get
                method = self._request(call, method_name=rpc.path)
                setattr(self, name, method)
        else:
            self._request_handler = LocalRPCRequestCall(service_location)

            calls = iface._get_class_calls()
            for rpc in calls.values():
                name = rpc.path.replace('-', '_')

                call = self._request_handler.call
                method = self._request(call, method_name=rpc.__name__)
                setattr(self, name, method)
