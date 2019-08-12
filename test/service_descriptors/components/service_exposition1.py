from pyservices.context import Context
from pyservices.data_descriptors.meta_model import MetaModel
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RestResourceInterface, \
    RPCInterface, RPC, HTTPExposition

from pyservices.data_descriptors.fields import StringField

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper']
COMPONENT_KEY = __name__


class ServiceEx1(Service):
    service_base_path = 'service-ex1'

    class RPC_ex(RPCInterface):
        if_path = 'expo'

        def my_dep_op(self):
            return True

        @RPC(exposition=HTTPExposition.FORBIDDEN)
        def my_forbidden_op(self):
            return True


def register_component(ctx: Context):
    service = ServiceEx1()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)
