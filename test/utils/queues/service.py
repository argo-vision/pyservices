from pyservices.service_descriptors.interfaces import EventInterface, event
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.utils.queues import QueuesType


class Test(Service):
    service_base_path = 'test'
    if_path = 'test'  # NOTE: shared with RPC

    class Events(EventInterface):
        queue_type = QueuesType.NOT_PERSISTENT
        if_path = "events"

        @event(path="test-queue")
        def test_queue(self):
            return "processed"

        @event(path="test-queue-with-param")
        def test_queue_with_param(self, param):
            return "processed_param"