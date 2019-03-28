import falcon
import requests
import hashlib

from wsgiref import simple_server
from threading import Thread
from typing import Union

from pyservices.frameworks import FalconResourceGenerator, FALCON
from pyservices.layer_supertypes import Service


# TODO docs
class RestClient:
    """ Generate a client proxy.

    It generated when the rest server is initialized.

    Class attributes:
        clients (dict): Contains the client of different services, the key
            are the URI of the resource.
    """
    clients = {}

    def __init__(self, service: Service):
        """ Initialize a REST client proxy.
        TODO: interfaces used to access
        Arguments:
             TODO
        """
        # TODO save config ??
        service_path = service.get_service_path()
        resources = service.get_rest_resources()
        self.interfaces = {}
        self.resources_names = []
        for uri, res in resources.items():
            self.resources_names.append(uri)
            self.interfaces[uri] = RestResourceEndPoint(
                f'{service_path}/{uri}', res)
            RestClient.clients[service_path] = self


# TODO docs
class RestResourceEndPoint:
    """ Represent the object used to perform actual REST calls for a given
        resource.

    """
    def __init__(self, path, res):
        """ Initialize the end point"""
        self.path = path
        self.codec = res.codec
        self.meta_model = res.meta_model

    def collect(self):
        return self.codec.decode(requests.get(self.path).content,
                                 self.meta_model)

    def detail(self, res_id):
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())
        return self.codec.decode(requests.get(f'{self.path}/{res_id}').content,
                                 self.meta_model)

    def add(self, resource):
        resource = self.codec.encode(resource)
        requests.put(self.path, resource)
        return True

    def delete(self, res_id):
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())
        requests.delete(f'{self.path}/{res_id}')
        return True

    def update(self, res_id, resource):
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())
        resource = self.codec.encode(resource)
        requests.post(f'{self.path}/{res_id}', resource)
        return True


# TODO be more generic, abstract for other type of interfaces
# TODO docs
class RestGenerator:
    _clients = dict()
    _servers = dict()

    @classmethod
    def config_identifier(cls, config):
        # TODO
        return hashlib.md5(str(sorted(config.items())).encode()).digest()

    # TODO design pattern...
    @classmethod
    def get_client_proxy(cls, service_repr: Union[dict, Service]):
        if isinstance(service_repr, Service):
            config = service_repr.config
            service = service_repr
        elif isinstance(service_repr, dict):
            config = service_repr
            service = Service(service_repr)
        else:
            raise Exception  # TODO
        client = cls._clients.get(cls.config_identifier(config))
        if not client:
            client = RestClient(service)
            cls._clients[cls.config_identifier(config)] = client
        return client

    @classmethod
    def generate_rest_server(cls, service: Service):
        """ Generates the RESTFul gateway.

        """
        config = service.config
        server = cls._servers.get(cls.config_identifier(config))
        if server:
            raise Exception  # TODO
        else:
            base_path = config.get('service_base_path')
            framework = config.get('framework') or 'falcon'  # TODO handle default elsewhere
            resources = service.get_rest_resources()
            if framework == FALCON:
                app = application = falcon.API()
                falcon_resources = {
                    uri: FalconResourceGenerator(r).generate()
                    for uri, r in resources.items()}

                for uri, resources in falcon_resources.items():
                    path = f'/{base_path}/{uri}'
                    field_number = resources[1].id_dimension
                    res_path = '/'.join(['{{id_field_{}}}'.format(i)
                                         for i in range(field_number)])
                    app.add_route(path, resources[0])
                    app.add_route(f'{path}/{res_path}', resources[1])

                # TODO simple_server is temporary
                httpd = simple_server.make_server(config.get('address'),
                                                  int(config.get('port')),
                                                  application)
                t = Thread(target=httpd.serve_forever)
                t.start()
                # TODO is useful to cache this?
                cls._servers[cls.config_identifier(config)] = (t, httpd)
                return t, httpd
            else:
                raise NotImplementedError
