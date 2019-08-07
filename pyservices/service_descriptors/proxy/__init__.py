from collections import namedtuple

from pyservices.service_descriptors.interfaces import RestResourceInterface, RPCInterface
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.proxy.rest_proxy import RestDispatcherEndPoint
from pyservices.service_descriptors.proxy.rpc_proxy import RPCDispatcherEndPoint
from pyservices.utilities.exceptions import ServiceException


def create_service_connector(service, service_location):
    """ A remote client proxy.
        Args:
            service: The class which describes the Service.
            service_location : The service path. (E.g.
                protocol://address:port/service_name).
                Can be "local"
        """
    if not issubclass(service, Service):
        raise ServiceException(f'The service class is not a sublcass of  {Service} ')

    interfaces_endpoints = {}

    for iface in service.interfaces():
        if type(service_location) == str:
            loc = service_location
        else:
            descriptor_find = [x for x in service_location.interface_descriptors if isinstance(x, iface)]
            loc = descriptor_find[0]

        if issubclass(iface, RestResourceInterface):
            endpoint = RestDispatcherEndPoint(iface, loc)
        elif issubclass(iface, RPCInterface):
            endpoint = RPCDispatcherEndPoint(iface, loc)
        else:
            raise NotImplementedError

        iface_name = iface.get_endpoint_name()
        if iface_name in interfaces_endpoints:
            interfaces_endpoints[iface_name.replace('-', '_')]._merge_endpoints(endpoint)
        else:
            interfaces_endpoints[iface_name.replace('-', '_')] = endpoint

    interfaces_tuple = namedtuple('Interfaces', interfaces_endpoints.keys())
    return interfaces_tuple(**interfaces_endpoints)
