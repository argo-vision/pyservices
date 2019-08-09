# coding=utf-8
"""
Tests for handler
"""
from unittest import TestCase, mock
from unittest.mock import call

from pyservices.utilities.handlers import Handler


class TestHandler(TestCase):
    def test_feed_one_message(self):
        chain = mock.Mock()
        chain.return_value = "ok"
        message = mock.Mock()
        saver = mock.Mock()

        handler = Handler({'key': chain}, saver)
        handler.feed([message])

        chain.assert_called_once()
        self.assertEqual(call(message.data), chain.call_args)
        saver.save.assert_called_once_with({'key': 'ok'}, message)

    def test_feed_error_in_processing(self):
        chain = mock.Mock()
        chain.side_effect = Exception("boom")
        message = mock.Mock()
        saver = mock.Mock()

        handler = Handler({'key': chain}, saver)
        handler.feed([message])

        chain.assert_called_once()
        message.nack.assert_called_once()
        self.assertEqual(call(message.data), chain.call_args)
        saver.save.assert_not_called()

    def test_feed_two_message_but_one_fail(self):
        chain = mock.Mock()
        chain.side_effect = ["ciao", Exception("boom")]
        message1 = mock.Mock()
        message2 = mock.Mock()
        saver = mock.Mock()

        handler = Handler({'key': chain}, saver)
        handler.feed([message1, message2])

        saver.save.assert_called_once_with({'key': "ciao"}, message1)
