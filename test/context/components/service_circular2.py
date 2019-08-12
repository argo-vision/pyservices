from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service
from test.context.components.configuration import get_path

COMPONENT_DEPENDENCIES = [get_path('service_circular1')]
COMPONENT_KEY = __name__


class ServiceCircular2(Service):
    pass


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, ServiceCircular2())
