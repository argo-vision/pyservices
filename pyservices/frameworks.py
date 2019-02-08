import collections
import inspect
import logging

import falcon

from pyservices import entity_codecs
from pyservices.data_descriptors import ComposedField
from pyservices.exceptions import HTTPNotFound

logger = logging.getLogger(__package__)

# REST Framework
FALCON = 'falcon'


class FalconResourceGenerator:
    """Builder class used to produce Falcon-like Resources."""

    def __init__(self, iface):
        """Initialize the meta model.

        Attributes:
            iface (pyservices.interfaces.Restful): The interface from which the
                Falcon Resources are generated
        """
        self.meta_model = iface.meta_model
        self.codec = iface.codec or entity_codecs.JSON

        methods = {name_method[0]: name_method[1]
                   for name_method in inspect.getmembers(
                iface, lambda m: inspect.ismethod(m))}
        collect_methods_names = filter(
            lambda k: k.startswith('collect'), methods)
        self.collect = sorted([methods.get(n) for n in collect_methods_names],
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
            logger.error("{} returns a something that is not of the model type"
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
        return (
            type(f'{FALCON}{self.meta_model.name}s', (object,), {
                'on_get': self._resource_collection_get,
                'on_put': self._resource_collection_put}),
            type(f'{FALCON}{self.meta_model.name}', (object,), {
                'on_get': self._resource_get,
                'on_post': self._resource_post,
                'on_delete': self._resource_delete,
                'id_dimension': len(
                    self.meta_model.primary_key_field.meta_model.fields)
                if isinstance(self.meta_model.primary_key_field, ComposedField)
                else 1}))
