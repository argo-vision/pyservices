from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service


COMPONENT_DEPENDENCIES = ['not_a_component']
COMPONENT_KEY = __name__


class BrokenService(Service):
    pass


def register_component(ctx: Context):
    pass
