import falcon
import inspect

from pyservices import entity_codecs
from pyservices.exceptions import InterfaceDefinitionException


# TODO refactor

# REST Framework
FALCON = 'Falcon'


class FalconResourceGenerator:
    """Builder class used to produce Falcon-like Resources."""
    def __init__(self, iface):
        """Initialize the meta model.

        Attributes:
            iface (pyservices.interfaces.Restful): The inferface from which the
                Falcon Resources are generated
        """
        self.meta_model = iface.meta_model
        self.codec = iface.codec or entity_codecs.JSON

        methods = {name_method[0]: name_method[1]
                   for name_method in inspect.getmembers(
            iface, lambda m: inspect.isfunction(m))}
        self.collection = methods.get('collection')
        self.add = methods.get('add')
        self.detail = methods.get('detail')
        self.update = methods.get('update')
        self.delete = methods.get('delete')

    def _collection_get(self, req, resp):
        resp.http_content_type = self.codec.http_content_type
        try:
            if self.collection:
                resp.body = self.codec.encode(
                    self.collection())
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException

    def _collection_put(self, req, resp):
        resp.http_content_type = self.codec.http_content_type

        try:

            if self.add:
                resource = self.codec.decode(
                    req.stream.read(),
                    self.meta_model)
                self.add(resource)
                resp.status = falcon.HTTP_CREATED
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException

    def _resource_get(self, req, resp, res_id):
        resp.http_content_type = self.codec.http_content_type

        try:
            if self.detail:
                resp.body = self.codec.encode(
                    self.detail(res_id))
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException

    def _resource_post(self, req, resp, res_id):
        resp.http_content_type = self.codec.http_content_type

        try:
            if self.update:
                resource = self.codec.decode(
                    req.stream.read(),
                    self.meta_model)
                self.update(res_id, resource)
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException

    def _resource_delete(self, req, resp, res_id):
        resp.http_content_type = self.codec.http_content_type

        try:
            if self.delete:
                self.delete(res_id)
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException

    def generate(self):
        return (
            type(f'{FALCON}{self.meta_model.name}s', (object,), {
                'on_get': self._collection_get,
                'on_put': self._collection_put
            }),
            type(f'{FALCON}{self.meta_model.name}', (object,), {
                'on_get': self._resource_get,
                'on_post': self._resource_post,
                'on_delete': self._resource_delete,
            }))
