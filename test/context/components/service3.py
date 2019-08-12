from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper']
COMPONENT_KEY = __name__


class Service3(Service):
    service_base_path = 'Service3'


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service3())
