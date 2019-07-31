from pyservices.context import Context
from ..configuration import get_path
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks',
                          get_path('component1')]
COMPONENT_KEY = __name__


class Service2(Service):
    pass


def register_component(ctx: Context):
    pass
