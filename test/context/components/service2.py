from pyservices.context import Context
from ..configuration import get_path
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks',
                          get_path('component1'), get_path('service1')]
COMPONENT_KEY = __name__


class Service2(Service):
    service_base_path = 'Service2'
    pass


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service2())

