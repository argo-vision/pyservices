from pyservices.context import Context
from pyservices.data_descriptors.meta_model import MetaModel
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RestResourceInterface, \
    RPCInterface, RPC, HTTPExposition, HTTP_op

from pyservices.data_descriptors.fields import StringField

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper']
COMPONENT_KEY = __name__

book_mm = MetaModel('Book', StringField('title'), StringField('author'),
                    primary_key_name='title')
books = [book_mm.get_class()('Design patterns', 'GoF')]


class ServiceEx1(Service):
    service_base_path = 'service-ex1'

    class RESTEx(RestResourceInterface):
        meta_model = book_mm

        @HTTP_op(exposition=HTTPExposition.MANDATORY)
        def detail(self, res_id):
            # This is exposed in PRODUCTION
            return books[0]

        @HTTP_op(exposition=HTTPExposition.FORBIDDEN)
        def collect(self):
            # This is not exposed in PRODUCTION
            return books

    class RPCEx(RPCInterface):
        if_path = 'expo'

        def my_dep_op(self):
            return True

        @HTTP_op(exposition=HTTPExposition.FORBIDDEN)
        def my_forbidden_op(self):
            return True


def register_component(ctx: Context):
    service = ServiceEx1()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)
