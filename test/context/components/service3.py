from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_KEY = __name__


class Service3(Service):
    service_base_path = 'Service3'

    def __init__(self, ctx):
        super().__init__(ctx)


COMPONENT_DEPENDENCIES = Service3.dependencies()


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service3(ctx))
