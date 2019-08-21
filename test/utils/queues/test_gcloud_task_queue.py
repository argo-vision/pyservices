# coding=utf-8
"""
Tests for puller
"""
import json
import unittest
import urllib

from google.cloud import tasks_v2

from pyservices.utils.queues import GcloudTaskQueue
from test.utils.queues.gcloud_fake_queue import _GcloudFakeQueue


class TestGcloudTaskQueue(unittest.TestCase):

    def setUp(self):
        tasks_v2.CloudTasksClient = _GcloudFakeQueue
        self.parent_parameters = {"project": "project_test", "location": "location_test",
                                  "queue": "queue_test"}
        self.gcloud_task_queue = GcloudTaskQueue(**self.parent_parameters)

    def test_parent_queue(self):
        self.assertEqual(self.gcloud_task_queue.parent,
                         self.gcloud_task_queue.client.queue_path(**self.parent_parameters))

    def test_add_get_task_without_params(self):
        expected_url = "/"
        expected_args = {}
        task = {"method": "GET", "relative_url": expected_url}
        expected_name = 'Fake gcloud task'

        response = self.gcloud_task_queue.add_task(task)

        self.assertEqual(response.name, expected_name)
        self.assertEqual(response.task['url'], expected_url)
        self.assertEqual(response.task['args'], expected_args)

    def test_add_get_task_with_params(self):
        url = "/"
        expected_args = {}
        expected_params = {'test': 'test', 'two_test': 'two_test'}
        expected_url = url + "?" + urllib.parse.urlencode(expected_params)
        task = {"method": "GET", "relative_url": url, "data": expected_params}
        expected_name = 'Fake gcloud task'

        response = self.gcloud_task_queue.add_task(task)

        self.assertEqual(response.name, expected_name)
        self.assertEqual(response.task['url'], expected_url)
        self.assertEqual(response.task['args'], expected_args)

    def test_add_post_task(self):
        expected_url = "/"
        expected_body = {"test": "test"}
        json_expected_body = {'data': json.dumps(expected_body, default=str).encode()}
        task = {"method": "post", "relative_url": expected_url, "data": expected_body}
        expected_name = 'Fake gcloud task'

        response = self.gcloud_task_queue.add_task(task)

        self.assertEqual(response.name, expected_name)
        self.assertEqual(response.task['url'], expected_url)
        self.assertEqual(response.task['args'], json_expected_body)
