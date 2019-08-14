from pyservices.context import Context
from pyservices.data_descriptors.meta_model import MetaModel
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RestResourceInterface, \
    RPCInterface, RPC, HTTPExposition, HTTP_op

from pyservices.data_descriptors.fields import StringField
from test.service_descriptors.uservices import get_path

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper',
                          get_path('service_exposition1')]
COMPONENT_KEY = __name__


class ServiceEx3(Service):
    service_base_path = 'service-ex3'

    class RPC_ex(RPCInterface):
        if_path = 'expo'

        def my_op(self):
            return True

        @HTTP_op(exposition=HTTPExposition.MANDATORY)
        def my_mandatory_op(self):
            return True


def register_component(ctx: Context):
    service = ServiceEx3()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)
