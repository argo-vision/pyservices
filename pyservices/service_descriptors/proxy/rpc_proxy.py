import json

import requests

from pyservices.service_descriptors.proxy.proxy_interface import EndPoint
from pyservices.utilities.exceptions import ClientException


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
        except Exception:
            raise ClientException('Exception on request')

        self._check_message_status(resp)
        return json.loads(resp.content) if resp.content else None

    def get(self, path, data):
        try:
            resp = requests.get(self.path(path), params=data, timeout=5)
        except Exception:
            raise ClientException('Exception on request')

        self._check_message_status(resp)
        return json.loads(resp.content) if resp.content else None

    def _check_message_status(self, resp):
        if resp is not None and resp.status_code == 403:
            raise ClientException('Forbidden request')
        if resp is None:
            raise ClientException("Response is empty")
        if not str(resp.status_code).startswith('2'):
            raise ClientException("Not a 2xx")


class RPCDispatcherEndPoint(EndPoint):
    def _request(self, http_method, method_name):

        def RPC_request(**kwargs):
            # TODO A check could be made if kwargs matches the call
            return http_method(path=method_name, data=kwargs)

        return RPC_request

    def __init__(self, iface, service_location):
        if service_location == 'local':
            pass
            # self._request_conrext_manager = local_request_call
            # self._iface_location = service_location
        else:
            iface_location = f'{service_location}/{iface.get_endpoint_name()}'
            self._request_handler = RemoteRPCRequestCall(iface_location)

        calls = iface.get_call_descriptors()
        for rpc in calls.values():
            name = rpc.path.replace('-', '_')

            if rpc.method == 'post':
                call = self._request_handler.post
            else:
                call = self._request_handler.get
            method = self._request(call, method_name=rpc.path)
            setattr(self, name, method)
