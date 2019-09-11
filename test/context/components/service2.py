from pyservices.context import Context
from test.context.uservices import get_path
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper',
                          get_path('component1'), get_path('service1')]
COMPONENT_KEY = __name__


class Service2(Service):
    service_base_path = 'Service2'

    def __init__(self, ctx):
        super().__init__(ctx)


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service2(ctx))

