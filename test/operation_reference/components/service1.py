from pyservices.service_descriptors.interfaces import RPCInterface
from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks']
COMPONENT_KEY = __name__


class Service1(Service):
    service_base_path = 'Service1'
    if_path = 'service'

    class Test(RPCInterface):
        if_path = 'test'

        def test_method_reference(self):
            return "Processecs"


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, Service1())
