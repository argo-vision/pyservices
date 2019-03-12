import inspect
import falcon
import requests

from abc import ABC
from wsgiref import simple_server
from threading import Thread

import pyservices as ps
from pyservices.interfaces import RestfulResource
from pyservices.frameworks import FalconResourceGenerator


# TODO remove
class Model(ABC):
    pass


class Service:
    """Base class for implementing a service
    """
    def __init__(self, config: dict = None):
        """Initialize the service instance.

        Attributes:
            config (dict): The configuration of the service.
        """
        self.config = config
        self._interfaces = {}

    def rest_server(self):
        """Generates the RESTFul gateway.
        """

        # generate single for all the interface of all rest resources
        iface = self._interfaces.get(RestfulResource.interface_type_id)
        if iface:
            return iface
        else:
            port = self.config.get('port') or 7890
            address = self.config.get('address') or 'localhost'
            framework = self.config.get('framework') or 'falcon'
            members = inspect.getmembers(self,
                                         lambda m:
                                         inspect.isclass(m) and issubclass(
                                             m, RestfulResource))
            resources = {
                res[1].resource_path or f'{res[1].meta_model.name.lower()}s': res[1]
                for res in members}
            base_path = self.__class__.base_path
            RestClient(f'http://{address}:{port}/{base_path}', resources)
            if framework == ps.frameworks.FALCON:
                app = application = falcon.API()
                falcon_resources = {uri: FalconResourceGenerator(r).generate()
                                    for uri, r in resources.items()}

                for uri, resources in falcon_resources.items():
                    path = f'/{base_path}/{uri}'
                    app.add_route(path, resources[0])
                    app.add_route(path + '/{res_id}', resources[1])
                httpd = simple_server.make_server(address, port, application)
                t = Thread(target=httpd.serve_forever)
                t.start()
                self._interfaces[RestfulResource.interface_type_id] = (t, httpd)
                return t, httpd
            else:
                raise NotImplementedError

    def rest_client(self):
        """Get a client proxy

        TODO there is only one instance of the RestClient given a resource
        """
        port = self.config.get('port') or 7890
        address = self.config.get('address') or 'localhost'
        base_path = self.__class__.base_path
        return RestClient.clients.get(f'http://{address}:{port}/'
                                      f'{base_path}')


class RestClient:
    """ Generate a client proxy.

    It generated when the rest server is initialized.

    Class attributes:
        clients (dict): Contains the client of different services, the key
            are the URI of the resource.
    """
    clients = {}

    def __init__(self, service_path, resources):
        """ Initialize a REST client proxy.

        Arguments:
            service_path (str): The URI of the resource service with the
                information regarding the service, the port and the address
            resources (dict): The keys are the name of the resources, the values
                are the resources themselves
        """
        self.interfaces = {}
        self.resources_names = []
        for uri, res in resources.items():
            self.resources_names.append(uri)
            self.interfaces[uri] = RestResourceEndPoint(
                f'{service_path}/{uri}', res)
            RestClient.clients[service_path] = self


class RestResourceEndPoint:
    """ Represent the object used to perform actual REST calls for a given
        resource.

    """
    def __init__(self, path, res):
        """ Initialize the end point"""
        self.path = path
        self.codec = res.codec
        self.meta_model = res.meta_model

    def get_collection(self):
        return self.codec.decode(requests.get(self.path).content,
                                 self.meta_model)

    def get_detail(self, res_id):
        return self.codec.decode(requests.get(f'{self.path}/{res_id}').content,
                                 self.meta_model)

    def add(self, resource):
        resource = self.codec.encode(resource)
        requests.put(self.path, resource)
        return True

    def delete(self, res_id):
        requests.delete(f'{self.path}/{res_id}')
        return True

    def update(self, res_id, resource):
        resource = self.codec.encode(resource)
        requests.post(f'{self.path}/{res_id}', resource)
        return True
