# coding=utf-8
"""
Tests for puller
"""
import unittest
from unittest import mock

from pyservices.utilities.pullers import Puller
from pyservices.utilities.queues import Queue


class TestPuller(unittest.TestCase):

    def test_simple_counter(self):
        handler = mock.Mock()

        queue = Queue()

        puller = Puller(queue, handler)
        puller.start()
        self.assertIsNotNone(puller._worker)
        # double start should not be a problem
        puller.start()

        for i in range(10):
            queue.put(1)

        self.assertIsNotNone(puller._worker)
        puller.stop()

        handler.feed.assert_called()
        self.assertEqual(10, handler.feed.call_count)
        self.assertIsNone(puller._worker)

        # double stop should not be a problem
        puller.stop()
        self.assertIsNone(puller._worker)
