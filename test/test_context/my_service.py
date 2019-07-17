from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.interfaces import RPCInterface, \
    RestResourceInterface
from pyservices.context import Context
COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.frameworks']
COMPONENT_KEY = __name__


class MyService(Service):
    service_base_path = 'user-manager'

    class UserREST(RestResourceInterface):
        if_path = 'users'

        def collect(self):
            return []

    class UserRPC(RPCInterface):
        if_path = 'users'

        def login(self, email, password):
            return 'TOKEN'


def register_component(ctx: Context):
    service = MyService({})
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)  # FIXME: MOVE ME I don't have enough knowledge HERE
