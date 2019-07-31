from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service
from test.context.configuration import get_path

COMPONENT_DEPENDENCIES = [get_path('service_circular2')]
COMPONENT_KEY = __name__


class ServiceCircula1(Service):
    pass


def register_component(ctx: Context):
    pass
