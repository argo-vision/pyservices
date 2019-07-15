# TODO refactor imports
import hashlib
import itertools
import re
from collections import namedtuple
from contextlib import contextmanager
from threading import Thread
from wsgiref import simple_server

import falcon
import requests

# TODO refactor imports
import pyservices as ps
from pyservices.data_descriptors.entity_codecs import Codec, JSON
from pyservices.exceptions import ServiceException, ClientException
from pyservices.service_descriptors.frameworks import FalconResourceGenerator, FALCON
from pyservices.service_descriptors.interfaces import RestResource
from pyservices.service_descriptors.layer_supertypes import Service


class RestClient:
    """ A client proxy.

    Class attributes:
        clients (dict): Contains the client of different services, the key
            are the URI of the resource.
    """

    def __init__(self, service_path: str, service_class, codec: Codec):
        """ Initialize a REST client proxy.

        Args:
             service_path (str): The service path. (E.g.
                protocol://address:port/service_name)
            service_class: The class which describes the Service.
            codec (Codec): The codec used for the communication # TODO it's likely that this will be moved in the dependencies
        """
        if not issubclass(service_class, Service):
            raise ServiceException(f'The service class is not a {Service} '
                                   f'instance.')
        service_path = service_path
        resources = service_class.get_rest_resources_meta_models()
        resources_names = []
        interfaces = {}
        for n, mm in resources.items():
            resources_names.append(n)
            interfaces[n] = RestResourceEndPoint(
                f'{service_path}/{n}', mm, codec)

        interfaces_tuple = namedtuple('Interfaces', resources_names)
        self.interfaces = interfaces_tuple(**interfaces)


class RestResourceEndPoint:
    """ Represent the object used to perform actual REST calls on a given
        resource.
    """

    def __init__(self, path, meta_model, codec):
        """ Initialize the end point.
        """
        self.path = path
        self.codec = codec
        self.meta_model = meta_model

    @staticmethod
    @contextmanager
    def _requests_call(method, path, **kwargs):
        """ Wrapper used to perform requests and checks.

        """
        resp = None
        try:
            resp = method(path, **kwargs)
            yield resp
        except Exception:
            raise ClientException('Exception on request')

        finally:
            # TODO more status codes could be handled
            if resp is not None and resp.status_code == 403:
                raise ClientException('Forbidden request')
            if resp is None:
                raise ClientException("Response is empty")

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
        with RestResourceEndPoint._requests_call(
                requests.get, path=self.path, params=params) as resp:
            if resp.status_code == 200:
                data = self.codec.decode(resp.content, self.meta_model)
                return data

    def detail(self, res_id):
        # FIXME: this should be a primary key for the model
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        path = f'{self.path}/{res_id}'

        with RestResourceEndPoint._requests_call(
                requests.get, path=path) as resp:
            if resp.status_code == 200:
                data = self.codec.decode(resp.content, self.meta_model)
                return data

    def add(self, resource):
        if not isinstance(resource, self.meta_model.get_class()):
            raise ValueError('Expected a {}'.format(self.meta_model.name))
        resource = self.codec.encode(resource)
        with RestResourceEndPoint._requests_call(
                requests.put, path=self.path, data=resource) as resp:

            if resp.status_code == 201:
                loc = resp.headers['location']
                res_id = loc.replace(resp.request.path_url + '/', '')
                # FIXME: this should be maybe a primary key?
                return res_id

        raise RuntimeError("Server side exception")

    def delete(self, res_id):
        # FIXME: res_id should be a primary key for the model
        if isinstance(res_id, dict):
            res_id = "/".join(res_id.values())

        path = f'{self.path}/{res_id}'

        with RestResourceEndPoint._requests_call(
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
        with RestResourceEndPoint._requests_call(
                requests.post, path=path, data=resource) as resp:
            if resp.status_code == 200:
                return True


class RestGenerator:
    """ Class used to generate the rest server and client.
    """
    _servers = dict()

    @classmethod
    def config_identifier(cls, config):
        return hashlib.md5(str(sorted(config.items())).encode()).digest()  # TODO #config

    @classmethod
    def get_client_proxy(cls, service_address: str, service_port: str,
                         service_base_path: str, service_class,
                         codec: Codec = JSON) -> RestClient:
        """ Method used to generate a REST client.
        """
        service_path = f'http://{service_address}:{service_port}/' \
            f'{service_base_path}'
        client = RestClient(service_path, service_class, codec)
        return client

    @classmethod
    def generate_rest_server(cls, service: Service):
        """ Generates the RESTFul gateway.

        """
        config = service.config
        server = cls._servers.get(cls.config_identifier(config))  # TODO config
        if server:
            raise ServiceException('The service with that configuration is '
                                   'already initialized.')
        else:
            base_path = config.get('service_base_path')
            address = config.get('address')
            port = int(config.get('port'))
            framework = config.get('framework') or 'falcon'  # TODO config / handle defaults elsewhere
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

                # Logging registered uris
                registered_uris = [x.uri_template for x in app._router._roots
                                   if x.uri_template is not None]
                children = itertools.chain.from_iterable((x.children for x in app._router._roots))
                registered_uris += [x.uri_template for x in children]
                for uri in registered_uris:
                    ps.log.info("Registered: {}".format(uri))

                # TODO simple_server is temporary
                httpd = simple_server.make_server(address, port, application,
                                                  handler_class=Handler)
                ps.log.info(f'Serving {base_path} on {address} port {port}')

                t = Thread(target=httpd.serve_forever)
                t.start()
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
