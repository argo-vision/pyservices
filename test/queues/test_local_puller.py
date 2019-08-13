# coding=utf-8
"""
Tests for puller
"""
import unittest
from unittest.mock import Mock

from pyservices.service_descriptors.layer_supertypes import ServiceOperationReference
from pyservices.utilities.pullers import Puller
from pyservices.utilities.queues import Queue


class TestLocalPuller(unittest.TestCase):

    def test_simple_counter(self):
        queue = Queue()
        queue._puller = Puller(queue)
        queue._puller.start()

        self.assertIsNotNone(queue._puller._worker)

        queue._puller.stop()

    def test_queue_puller(self):
        handler = Mock()
        queue = Queue()
        queue._puller = Puller(queue)
        TestLocalPuller.mock_reference(handler.feed)

        TestLocalPuller.fill_queue(queue)
        queue._puller.start()
        queue._puller.stop()

        self.assertEqual(10, handler.feed.call_count)

    def test_invalid_data(self):
        handler = Mock()
        queue = Queue()
        queue._puller = Puller(queue)
        TestLocalPuller.mock_reference(handler.feed)

        TestLocalPuller.add_invalid_task(queue)
        queue._puller.start()
        queue._puller.stop()

        self.assertEqual(0, handler.feed.call_count)

    @staticmethod
    def mock_reference(call):
        ServiceOperationReference.get_service = Mock()
        ServiceOperationReference.get_interface = Mock()
        ServiceOperationReference.get_method = call

    @staticmethod
    def fill_queue(queue):
        for i in range(10):
            task = queue.build_task("test", "test", "test", data=[1, 2, 3])
            queue.add_task(task)
        return None

    @staticmethod
    def add_invalid_task(queue):
        queue.get = Mock()
        queue.get.return_value = queue.Message(None, queue)
