from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service
from test.context.configuration import get_path

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks']
COMPONENT_KEY = __name__


class Service3(Service):
    service_base_path = 'Service3'


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service3())
