import json
import logging
import urllib
from multiprocessing import Pipe

import requests
from persistqueue import FIFOSQLiteQueue

from pyservices.utilities import gcloud
from pyservices.utilities.pullers import GcloudFakeQueuePuller

logger = logging.getLogger(__package__)


class SqlLiteQueue:
    """
    A simple queue that use a sql lite db
    """

    class Message:
        """
        The message used by the queue
        """

        def __init__(self, data, queue):
            self.data = data
            self._queue = queue

        def ack(self):
            """
            To call on success
            """
            self._queue.task_done()

        def nack(self):
            """
            To call on failure
            """
            self._queue.put(self.data)
            self._queue.task_done()

    def __init__(self, config):
        self._q = FIFOSQLiteQueue(path=config['QUEUE_PATH'], multithreading=True)

    def put(self, value):
        """
        Put a value in the queue
        :param value: Value to put in the queue
        """
        self._q.put(value)

    def get(self):
        """
        Get a value from the queue
        :return: A Message containing a value that was in the queue
        """
        data = self._q.get()
        return self.Message(data, self._q)


class Queue:
    """
    A concurrent queue multi producer single consumer.
    """

    class Message:
        """
        The message used by the queue
        """

        def __init__(self, data, queue):
            self.data = data
            self._queue = queue

        def ack(self):
            """
            To call on success
            """
            pass

        def nack(self):
            """
            To call on failure
            """
            pass

    def __init__(self):
        (self._sx, self._rx) = Pipe()

    def put(self, value):
        """
        Put a value in the queue
        :param value: Value to put in the queue
        """
        self._sx.send(value)

    def get(self):
        """
        Get a value from the queue
        :return: A Message containing a value that was in the queue
        """

        data = self._rx.recv()
        # FIXME: FIXME: FIXME: this is really bad too
        return self.Message(data, self)


class GcloudTaskQueue:
    """Wrapper for gcloud task queue rest interface """

    def __init__(self, project_id, location_id, queue_id):
        """ Initialize the gcloud task queue

        Attributes:
            project_id (str): project id from gcloud console
            location_id (str): location of the appengine application
            queue_id (str) : queue name. Queue must be created from gcloud sdk


        Gcloud sdk CLI:
        More info at: https://cloud.google.com/tasks/docs/creating-queues

        Create task queue:
            gcloud tasks queues create [QUEUE_ID]

        Get task info:
            gcloud tasks queues describe [QUEUE_ID]

        List tasks:
            gcloud tasks queues list

        Update gcloud task queue to indicate service name:
            gcloud tasks queues update [QUEUE_ID] --routing-override=service:[SERVICE]


        """

        # Create a client.
        # client = CloudTasksClient()

        # Construct the fully qualified queue name.
        self.client = _GcloudFakeQueue()  # Fake queue for debug
        self.parent = self.client.queue_path(project_id, location_id, queue_id)

    def add_task(self, method, relative_url, data=None):
        """Create a task for GcloudTaskQueue

         Attributes:
                method (str): A http method ("GET" | "POST" | "PUT")
                relative_url (str): An url relative to the current gcloud project url
                    ([path] only of an url like service-dot-proejct.appspot.com/[path])
                data (dict): parameters to be appended to the url (for GET only) or
                    body of the task request (for POST and PUT only)

        """

        method = method.upper()
        # Construct the request body.
        task = {
            'app_engine_http_request': {  # Specify the type of request.
                'http_method': method,
                'url': relative_url
            }
        }

        if method in ["POST", "PUT"]:
            if data is None:
                data = {}
            task['app_engine_http_request']['body'] = json.dumps(data, default=str)
        elif method == "GET" and data is not None:
            parameters = urllib.parse.urlencode(data)
            task['app_engine_http_request']['url'] = '{}?{}'.format(relative_url, parameters)

        # Use the client to build and send the task.

        try:
            response = self.client.create_task(self.parent, task)
            response_str = 'Created task {}'.format(response['name'])
            logger.info(response_str)
            return response
        except Exception as ex:
            logger.info("Cannot add task to queue, error {}".format(ex))

    # def list_tasks(self):
    #    client = CloudTasksClient()
    #     parent = client.queue_path(**self.parent)
    #     tasks_iterator = client.list_tasks(parent)
    #     tasks = [t for t in tasks_iterator]
    #
    #     return tasks


class _GcloudFakeQueue:
    _queue = Queue()

    def __init__(self):

        self._puller = GcloudFakeQueuePuller(self._queue)
        self._puller.start()
        self._parent = []

    def queue_path(self, project_id, location_id, queue_id):
        self._parent = [project_id, location_id, queue_id]
        return self._parent

    def create_task(self, parent, task):
        assert (self._parent, parent)

        app_engine_http_request = task['app_engine_http_request']
        url = app_engine_http_request['url']
        http_method = app_engine_http_request['http_method']

        if http_method == "POST":
            kwargs = {'data': app_engine_http_request['body']}
            call = requests.post
        elif http_method == "PUT":
            kwargs = {'data': app_engine_http_request['body']}
            call = requests.put
        elif http_method == "GET":
            call = requests.get
            kwargs = {}
        else:
            raise NotImplementedError()

        final_task = {'call': call, 'url': url, 'args': kwargs}
        self._queue.put(final_task)

        response = {'name': "Fake gcloud task", 'task': final_task}
        return response


def get_queue():
    project_id = gcloud.get_project_id()
    location_id = gcloud.get_location_id()
    service_id = gcloud.get_service_id()
    return GcloudTaskQueue(project_id, location_id, service_id)
