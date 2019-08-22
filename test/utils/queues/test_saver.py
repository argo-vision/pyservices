# coding=utf-8
"""
Tests for saver
"""
import datetime
import unittest
from unittest import mock

#from pymongo.errors import DuplicateKeyError
from pymongo.errors import DuplicateKeyError

from pyservices.utils.savers import Saver


class TestSaver(unittest.TestCase):
    def test_save(self):
        message = mock.Mock()
        dba = mock.Mock()
        saver = Saver(dba)
        saver.save({'id': {'timestamp': datetime.datetime.now()}, 'a': {'f': 1}}, message)

        dba.insert_one.assert_called_once()
        message.ack.assert_called()
        message.nack.assert_not_called()

    def test_save_two_in_results(self):
        message = mock.Mock()
        dba = mock.Mock()
        saver = Saver(dba)
        saver.save({'id': {'timestamp': datetime.datetime.now()}, 'a': {'f': 1}, 'b': {'e': 2}}, message)

        dba.insert_one.assert_called_once()

        message.ack.assert_called()
        message.nack.assert_not_called()

    def test_save_duplicated(self):
        message = mock.Mock()
        dba = mock.Mock()
        exception = mock

        dba.insert_one.side_effect = DuplicateKeyError(error=1)
        saver = Saver(dba)
        saver.save({'id': {'timestamp': datetime.datetime.now()}, 'a': {'f': 1}, 'b': {'e': 2}}, message)

        dba.insert_one.assert_called_once()

        message.ack.assert_called()
        message.nack.assert_not_called()

    def test_save_exception(self):
        message = mock.Mock()

        dba = mock.Mock()

        dba.insert_one.side_effect = Exception
        saver = Saver(dba)

        saver.save({'id': {'timestamp': datetime.datetime.now()}, 'a': {'f': 1}, 'b': {'e': 2}}, message)

        dba.insert_one.assert_called_once()

        message.nack.assert_called()
        message.ack.assert_not_called()
