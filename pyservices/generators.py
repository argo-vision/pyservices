import falcon
import requests
import hashlib

from wsgiref import simple_server
from threading import Thread

import pyservices as ps
from pyservices.frameworks import FalconResourceGenerator, FALCON
from pyservices.layer_supertypes import Service
from pyservices.entity_codecs import Codec, JSON
from pyservices.interfaces import RestResource


# TODO docs
class RestClient:
    """ Generate a client proxy.

    It generated when the rest server is initialized.
    TODO
    Class attributes:
        clients (dict): Contains the client of different services, the key
            are the URI of the resource.
    """

    def __init__(self, service_path: str, service_class, codec: Codec):
        """ Initialize a REST client proxy.
        TODO: interfaces used to access
        Arguments:
             TODO
        """
        # TODO save config ??
        service_path = service_path
        resources = service_class.get_rest_resources_meta_models()
        self.interfaces = {}
        self.resources_names = []
        for n, mm in resources.items():
            self.resources_names.append(n)
            self.interfaces[n] = RestResourceEndPoint(
                f'{service_path}/{n}', mm, codec)


# TODO docs
class RestResourceEndPoint:
    """ Represent the object used to perform actual REST calls for a given
        resource.

    """
    def __init__(self, path, meta_model, codec):
        """ Initialize the end point"""
        self.path = path
        self.codec = codec
        self.meta_model = meta_model

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
        resp = requests.put(self.path, resource)
        loc = resp.headers['location']
        res_id = loc.replace(resp.request.path_url + '/', '')
        return res_id

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
    _servers = dict()

    @classmethod
    def config_identifier(cls, config):
        # TODO #CS
        return hashlib.md5(str(sorted(config.items())).encode()).digest()

    # TODO --> it's just a simple wrapper around RestClient
    @classmethod
    def get_client_proxy(cls, service_address: str, service_port: str,
                         service_base_path: str, service_class,
                         codec: Codec = JSON):
        service_path = f'http://{service_address}:{service_port}/' \
            f'{service_base_path}'
        client = RestClient(service_path, service_class, codec)
        return client

    @classmethod
    def generate_rest_server(cls, service: Service):
        """ Generates the RESTFul gateway.

        """
        config = service.config
        server = cls._servers.get(cls.config_identifier(config))  # TODO CS
        if server:
            raise Exception  # TODO
        else:
            base_path = config.get('service_base_path')
            address = config.get('address')
            port = int(config.get('port'))
            framework = config.get('framework') or 'falcon'  # TODO handle default elsewhere
            rest_resources = [iface_desc
                              for iface_desc in service.interface_descriptors
                              if isinstance(iface_desc, RestResource)]
            resources = {res.get_resource_name(): res for res in rest_resources}

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
                httpd = simple_server.make_server(address, port,application,
                                                  handler_class=Handler)
                ps.log.info(f'Serving {base_path} on {address} port {port}')

                t = Thread(target=httpd.serve_forever)
                t.start()
                # TODO is useful to cache this? #CS
                cls._servers[cls.config_identifier(config)] = (t, httpd)
                return t, httpd
            else:
                raise NotImplementedError


# TODO simple_server is temporary
class Handler(simple_server.WSGIRequestHandler):
    """ Wraps the default handler to avoid stderr logs
    """

    def log_message(self, *arg, **kwargs):
        ps.log.info("received {}: result {}".format(*arg[1:3]))

    def get_stderr(self, *arg, **kwargs):
        pass
