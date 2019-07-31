from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service

from test.context.configuration import get_path

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks', get_path('component1')]
COMPONENT_KEY = __name__


class Service1(Service):
    pass


def register_component(ctx: Context):
    pass
