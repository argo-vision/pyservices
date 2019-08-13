import abc
import json
import logging
import urllib
from enum import Enum
from multiprocessing import Pipe
from google.cloud import tasks_v2
from persistqueue import FIFOSQLiteQueue

from pyservices.utils.gcloud import check_if_gcloud, get_service_id, get_location_id, get_project_id
from pyservices.utils.pullers import Puller

logger = logging.getLogger(__package__)


class BaseQueue(abc.ABC):
    @staticmethod
    def initialize_and_run(configuration):
        pass

    @staticmethod
    def build_task(service, interface, method, data):
        pass

    @abc.abstractmethod
    def add_task(self, task):
        """
        Adding a task to the queue.

        Args:
            task (dict):    Task to add.

        Returns:
            Task ID.
        """

    @abc.abstractmethod
    def is_processing(self):
        """
        Checking if the current thread is processing a task.

        Returns:
            True if the current thread is processing a task.
        """


class SqlLiteQueue(BaseQueue):
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
            self._queue.add_task(self.data)
            self._queue.task_done()

    def __init__(self, config):
        self._q = FIFOSQLiteQueue(path=config['QUEUE_PATH'], multithreading=True)

    @staticmethod
    def initialize_and_run(configuration):
        return SqlLiteQueue(configuration)

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


class Queue(BaseQueue):
    """
    A concurrent queue multi producer single consumer.
    """
    _last_id = 0

    def _get_next_id(self):
        self._last_id += 1
        return self._last_id

    class Message:
        """
        The message used by the queue
        """

        def __init__(self, data, queue):
            self.data = data
            self._queue = queue
            self.id = id

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
        self._puller = None

    @staticmethod
    def initialize_and_run(_configuration):
        queue = Queue()
        queue._puller = Puller(queue)
        queue._puller.start()
        return queue

    @staticmethod
    def build_task(service, interface, method, data):
        service_method_reference = {'service_name': service.__class__.__name__,
                                    'interface_name': interface.__class__.__name__,
                                    'method_name': method.__name__}
        task = {'reference': service_method_reference, 'data': data}
        return task

    def add_task(self, task):
        """
        Put a value in the queue
        :param value: Value to put in the queue
        """
        if task is not None:
            task['id'] = self._get_next_id()
        self._sx.send(task)
        return task['id']

    def quit(self):
        self._sx.send(None)

    def get(self):
        """
        Get a value from the queue
        :return: A Message containing a value that was in the queue
        """

        data = self._rx.recv()
        # FIXME: FIXME: FIXME: this is really bad too
        return self.Message(data, self)

    def is_processing(self):
        return False


class GcloudTaskQueue(BaseQueue):
    """Wrapper for gcloud task queue rest interface """

    def __init__(self, project, location, queue):
        """ Initialize the gcloud task queue

        Attributes:
            project (str): project id from gcloud console
            location (str): location of the appengine application
            queue (str) : queue name. Queue must be created from gcloud sdk


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
        self.client = tasks_v2.CloudTasksClient()
        self.parent = self.client.queue_path(project, location, queue)

    @staticmethod
    def initialize_and_run(configuration):
        """
        Build a gcloud task queue using local environmennt settings
        Return
            gcloud_task_queue instance
        """
        project_id = get_project_id()
        location_id = get_location_id()
        service_id = get_service_id()
        return GcloudTaskQueue(project_id, location_id, service_id)

    def build_task(self, service, interface, method, data):
        task = {
            "method": method.http_method,
            "relative_url": f'{interface._get_endpoint()}/{method.path}',
            "data": data
        }
        return task

    def add_task(self, task):
        """Create a task for GcloudTaskQueue

         Attributes:
             task: dict with 3  values
                method (str): A http method ("GET" | "POST" | "PUT")
                relative_url (str): An url relative to the current gcloud project url
                    ([path] only of an url like service-dot-proejct.appspot.com/[path])
                data (dict): parameters to be appended to the url (for GET only) or
                    body of the task request (for POST and PUT only)

        """
        method = task['method'].upper()
        relative_url = task['relative_url']
        data = task['data'] if "data" in task else None

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

    def is_processing(self):
        from pyservices.service_descriptors.frameworks import request_info
        return 'AppEngine-Google' in request_info.user_agent


class QueuesType(Enum):
    """
    Exposition choices for an operation.
    NOTE: Expose all operations in development (also the forbidden ones).
    """
    NOT_PERSISTENT = 0
    PERSISTENT = 1


def get_queue(type: QueuesType, queue_configuration: {}):
    deploy_gcloud = check_if_gcloud()
    if deploy_gcloud:
        return GcloudTaskQueue.initialize_and_run(queue_configuration)
    else:
        if type == QueuesType.NOT_PERSISTENT:
            return Queue.initialize_and_run(queue_configuration)
        elif type == QueuesType.PERSISTENT:
            return SqlLiteQueue.initialize_and_run(queue_configuration)