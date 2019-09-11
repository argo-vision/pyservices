from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service
from test.context.uservices import get_path

COMPONENT_DEPENDENCIES = [get_path('service_circular2')]
COMPONENT_KEY = __name__


class ServiceCircular1(Service):
    def __init__(self, ctx):
        super().__init__(ctx)


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, ServiceCircular1(ctx))
