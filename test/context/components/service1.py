from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service

from test.context.uservices import get_path

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper', get_path('component1')]
COMPONENT_KEY = __name__


class Service1(Service):
    service_base_path = 'Service1'

    def __init__(self, ctx):
        super().__init__(ctx)


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service1(ctx))
