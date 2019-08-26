from pyservices.context import Context
from pyservices.service_descriptors.interfaces import RPC, \
    RestResourceInterface, RPCInterface, EventInterface, event, HTTP_op, HTTPExposition
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.utils.queues import QueuesType
from test.data_descriptors.meta_models import *

COMPONENT_DEPENDENCIES = ['pyservices.service_descriptors.WSGIAppWrapper']
COMPONENT_KEY = __name__


class Service4(Service):
    service_base_path = 'service4'
    if_path = 'notes'  # NOTE: shared with RPC

    class Events(EventInterface):
        queue_type = QueuesType.NOT_PERSISTENT
        if_path = "events"

        @HTTP_op(exposition=HTTPExposition.MANDATORY)
        @event(path="test-queue")
        def test_queue(self, arg1, arg2):
            print(arg1)
            return "processed"


def register_component(ctx: Context):
    service = Service4()
    ctx.register(COMPONENT_KEY, service)
    app = ctx.get_app()
    app.register_route(service)
