from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service

from test.context.configuration import get_path

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks', get_path('component1')]
COMPONENT_KEY = __name__


class Service1(Service):
    service_base_path = 'Service1'


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service1({}))

