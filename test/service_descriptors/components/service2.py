from pyservices.context import Context
from pyservices.service_descriptors.interfaces import RPCInterface
from pyservices.service_descriptors.layer_supertypes import Service

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper',
                          'test.service_descriptors.components.service1']
COMPONENT_KEY = __name__


class Service2(Service):
    service_base_path = 'Service2'

    def __init__(self, ctx):
        super().__init__(ctx)

    class Service1Connection(RPCInterface):
        if_path = 'external'

        def read_note(self):
            print(123)
            return self.service.dependencies['service1'].read_note()


def register_component(ctx: Context):
    service = Service2(ctx)
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)


