import falcon
import inspect

from pyservices import entity_codecs
from pyservices.exceptions import InterfaceDefinitionException
from pyservices.data_descriptors import ComposedField

# TODO refactor
# TODO work on robustness, exceptions, etc
# TODO rename collection_ and resource_

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

    def _collection_get(self, req, resp):
        resp.status = falcon.HTTP_404
        # TODO
        for collect in self.collect:
            # TODO  move in another method
            try:
                sg = inspect.signature(collect)
                sg.bind(**req.params)
            except TypeError:
                continue
            else:
                try:
                    resp.body = self.codec.encode(collect(**req.params))
                    resp.status = falcon.HTTP_200
                    resp.http_content_type = self.codec.http_content_type
                    return
                except Exception as e:  # TODO
                    raise InterfaceDefinitionException(
                        f'Error creating the restful interface - {e}')

    def _collection_put(self, req, resp):

        try:
            if self.add:
                resource = self.codec.decode(
                    req.stream.read(),
                    self.meta_model)
                res_id = self.add(resource)
                resp.status = falcon.HTTP_CREATED
                resp.location = f'{req.path}/{res_id}'
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException(
                'Error creating the restful interface')

    def _resource_get(self, req, resp, **kwargs):
        resp.http_content_type = self.codec.http_content_type
        res_id = self._validate_res_id(**kwargs)
        if not res_id:
            raise Exception  # TODO

        try:
            if self.detail:
                resp.body = self.codec.encode(
                    self.detail(res_id))
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException(
                'Error creating the restful interface')

    def _resource_post(self, req, resp, **kwargs):
        res_id = self._validate_res_id(**kwargs)
        if not res_id:
            raise Exception  # TODO

        try:
            if self.update:
                # TODO update requires all the non optional fields
                resource = self.codec.decode(
                    req.stream.read(),
                    self.meta_model)
                self.update(res_id, resource)
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException(
                'Error creating the restful interface')

    def _resource_delete(self, req, resp, **kwargs):
        res_id = self._validate_res_id(**kwargs)
        if not res_id:
            raise Exception  # TODO

        try:
            if self.delete:
                self.delete(res_id)
            else:
                resp.status = falcon.HTTP_404
        except Exception:
            raise InterfaceDefinitionException(
                'Error creating the restful interface')

    def _validate_res_id(self, **kwargs):
        return self.meta_model.validate_id(**kwargs)

    def generate(self):
        return (
            type(f'{FALCON}{self.meta_model.name}s', (object,), {
                'on_get': self._collection_get,
                'on_put': self._collection_put}),
            type(f'{FALCON}{self.meta_model.name}', (object,), {
                'on_get': self._resource_get,
                'on_post': self._resource_post,
                'on_delete': self._resource_delete,
                'id_dimension': len(
                    self.meta_model.primary_key_field.meta_model.fields)
                if isinstance(self.meta_model.primary_key_field, ComposedField)
                else 1}))
