from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service
from test.context.configuration import get_path

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks']
COMPONENT_KEY = __name__


class Service3(Service):
    pass


def register_component(ctx: Context):
    pass
