from pyservices.context import Context
from pyservices.service_descriptors.interfaces import RPCInterface
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks',
                          'test.service_descriptors.components.service1']
COMPONENT_KEY = __name__


class Service3(Service):
    service_base_path = 'Service3'

    class Service1Connection(RPCInterface):
        if_path = 'external'

        def read_note(self):
            self.service.dependencies['test']


def register_component(ctx: Context):
    service = Service3()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)


