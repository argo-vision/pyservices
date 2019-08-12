from pyservices.context import Context
from pyservices.data_descriptors.meta_model import MetaModel
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RestResourceInterface, \
    RPCInterface

from pyservices.data_descriptors.fields import StringField
from test.service_descriptors.components.configuration import get_path

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper',
                          get_path('service_exposition1')]
COMPONENT_KEY = __name__


class ServiceEx2(Service):
    pass


def register_component(ctx: Context):
    service = ServiceEx2()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)
