import collections
import inspect
import itertools
import logging

import falcon
from threading import Thread
from wsgiref import simple_server

import pyservices as ps
import abc

from pyservices.data_descriptors import entity_codecs
from pyservices.data_descriptors.fields import ComposedField
from pyservices.utilities.exceptions import HTTPNotFound
from pyservices.service_descriptors.interfaces import RestResourceInterface, \
    RPCInterface, HTTPInterface
from pyservices.context import Context


COMPONENT_DEPENDENCIES = []


logger = logging.getLogger(__package__)

# REST Framework
FALCON = 'falcon'


class FrameworkApp(abc.ABC):
    """ Base class for frameworks, it is used to crete WSGI applications.
    """
    def __init__(self):
        # TODO log
        self.app = None

    def register_route(self, service):
        pass

    @staticmethod
    def _get_interfaces(service):
        return [iface_desc
                for iface_desc in service.interface_descriptors
                if issubclass(iface_desc.__class__, HTTPInterface)]


class FalconApp(FrameworkApp):

    def __init__(self):
        super().__init__()
        self.app = falcon.API()

    def register_route(self, service):
        # get falcon rest resources
        resources = self._get_falcon_resource(service)

        # register routes and resources
        for uri, r in resources.items():
            path = f'/{service.service_base_path}/{uri}'
            self.app.add_route(path, r())

        self._log_registered_urls()

    def _get_falcon_resource(self, service):
        resources = {}
        for iface in FrameworkApp._get_interfaces(service):
            if isinstance(iface, RestResourceInterface):
                resources.update(self.RestResourceGenerator(iface).generate())
            elif isinstance(iface, RPCInterface):
                resources.update(self.RPCResourceGenerator(iface).generate())
        return resources

    def _log_registered_urls(self):
        # Logging registered uris
        registered_uris = [x.uri_template for x in self.app._router._roots
                           if x.uri_template is not None]
        children = itertools.chain.from_iterable(
            (x.children for x in self.app._router._roots))
        registered_uris += [x.uri_template for x in children]
        for uri in registered_uris:
            ps.log.info("Registered: {}".format(uri))

    class RPCResourceGenerator:
        """ TODO builder

        """

        def __init__(self, iface):
            self.iface = iface
            # name: method
            self.methods = iface._get_RPCs()

        @staticmethod
        def _falcon_handler_wrapper(
                function):  # TODO put this to an higher level abstraction
            def falcon_handler(self, req, res):
                try:
                    res.status_code = 200
                    function(req, res)
                except Exception as e:
                    res.status_code = 500

            return falcon_handler

        def generate(self):
            path = type(self.iface)._get_endpoint_name()
            res = dict()
            for method in self.methods:
                res[f'{path}/{method.path}'] = type(f'RPC{method.path}',
                                                    (object,), {
                                                        f'on_{method.http_method}': self._falcon_handler_wrapper(
                                                            method)
                                                    })
            return res

    class RestResourceGenerator:
        """Builder class used to produce Falcon-like REST Resources."""

        def __init__(self, iface):
            """Initialize the meta model.

            Attributes:
                iface (pyservices.interfaces.Restful): The interface from which the
                    Falcon Resources are generated
            """
            self.iface = iface
            self.meta_model = iface.meta_model
            self.codec = iface.codec or entity_codecs.JSON

            methods = {name_method[0]: name_method[1]
                       for name_method in inspect.getmembers(
                iface, lambda m: inspect.ismethod(m))}
            collect_methods_names = filter(
                lambda k: k.startswith('collect'), methods)
            self.collect = sorted(
                [methods.get(n) for n in collect_methods_names],
                key=lambda m: inspect.getsourcelines(m)[1])
            self.add = methods.get('add')
            self.detail = methods.get('detail')
            self.update = methods.get('update')
            self.delete = methods.get('delete')

        def _resource_collection_get(self, req, resp):
            def get_callable_collect():
                for c in self.collect:
                    try:
                        sg = inspect.signature(c)
                        sg.bind(**req.params)
                        return c
                    except TypeError:
                        continue

            collect = get_callable_collect()

            if collect is None:
                raise falcon.HTTPForbidden

            try:
                res = collect(**req.params)
            except Exception as e:
                logger.error("{} operation has failed: {}"
                             .format(collect.__name__, e))
                raise falcon.HTTPInternalServerError

            if not isinstance(res, collections.abc.Iterable):
                logger.error("{} return a non iterable object"
                             .format(collect.__name__))
                raise falcon.HTTPInternalServerError

            if not all(map(lambda x: isinstance(x, self.meta_model.get_class()),
                           res)):
                logger.error(
                    "{} returns a something that is not of the model type"
                    .format(collect.__name__))
                raise falcon.HTTPInternalServerError

            try:
                resp.body = self.codec.encode(res)
            except Exception as e:
                logger.error("Encoding operations has failed: {}".format(e))
                raise falcon.HTTPInternalServerError

            resp.status = falcon.HTTP_200
            resp.http_content_type = self.codec.http_content_type

        def _resource_collection_put(self, req, resp):
            if not self.add:
                raise falcon.HTTPForbidden

            try:
                resource = self.codec.decode(req.stream.read(), self.meta_model)
            except Exception as e:
                logger.error("Cannot decode the received model: {}".format(e))
                raise falcon.HTTPBadRequest

            try:
                res_id = self.add(resource)
            except Exception as e:
                logger.error("Cannot create resource: {}".format(e))
                raise falcon.HTTPInternalServerError

            resp.status = falcon.HTTP_CREATED
            resp.location = f'{req.path}/{res_id}'

        def _resource_get(self, req, resp, **kwargs):
            if not self.detail:
                raise falcon.HTTPForbidden

            resp.http_content_type = self.codec.http_content_type

            res_id = self.meta_model.validate_id(**kwargs)
            if res_id is None:
                raise falcon.HTTPNotFound

            try:
                detail = self.detail(res_id)
            except HTTPNotFound:
                raise falcon.HTTPNotFound
            except Exception as e:
                logger.error("Unexpected exception from detail: {}".format(e))
                raise falcon.HTTPInternalServerError

            if not isinstance(detail, self.meta_model.get_class()):
                logger.error("Detail returned an invalid model")
                raise falcon.HTTPInternalServerError

            try:
                resp.body = self.codec.encode(detail)
            except Exception as e:
                logger.error("Cannot encode data")
                raise falcon.HTTPInternalServerError

        def _resource_post(self, req, resp, **kwargs):
            if not self.update:
                raise falcon.HTTPForbidden

            res_id = self.meta_model.validate_id(**kwargs)
            if res_id is None:
                raise falcon.HTTPNotFound

            try:
                # TODO update requires all the non optional fields
                resource = self.codec.decode(req.stream.read(), self.meta_model)
            except Exception as e:
                logger.error("Cannot decode data: {}".format(e))
                raise falcon.HTTPBadRequest

            try:
                self.update(res_id, resource)
            except Exception as e:
                logger.error("Cannot update data: {}".format(e))
                raise falcon.HTTPInternalServerError

        def _resource_delete(self, req, resp, **kwargs):
            if not self.delete:
                raise falcon.HTTPForbidden

            res_id = self.meta_model.validate_id(**kwargs)
            if res_id is None:
                raise falcon.HTTPNotFound

            try:
                self.delete(res_id)
            except Exception as e:
                logger.error("Exception duing delete: {}".format(e))
                raise falcon.HTTPInternalServerError

            resp.status = falcon.HTTP_200

        def generate(self):
            path = type(self.iface)._get_endpoint_name()
            res = dict()
            res[path] = type(f'REST{self.meta_model.name}s', (object,), {
                'on_get': self._resource_collection_get,
                'on_put': self._resource_collection_put})

            if isinstance(self.meta_model.primary_key_field, ComposedField):
                id_dimension = len(
                    self.meta_model.primary_key_field.meta_model.fields)
            else:
                id_dimension = 1
            id_path = '/'.join(['{{id_field_{}}}'.format(i)
                                for i in range(id_dimension)])
            res[f'{path}/{id_path}'] = type(f'REST{self.meta_model.name}',
                                            (object,), {
                                                'on_get': self._resource_get,
                                                'on_post': self._resource_post,
                                                'on_delete': self._resource_delete})
            return res


def register_component(ctx: Context):
    app = FalconApp()  # TODO falcon is the only WSGI app supported
    ctx.register_app(app)  # TODO think about register_app (get_app)
