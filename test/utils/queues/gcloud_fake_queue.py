import threading
from typing import NamedTuple

import requests

from pyservices.utils.queues import Queue


class _GcloudFakeQueue:
    _queue = Queue()

    def __init__(self):
        self._puller = GcloudFakeQueuePuller(self._queue)
        self._parent = []

    def queue_path(self, project, location, queue):
        self._parent = [project, location, queue]
        return self._parent

    def create_task(self, parent, task):
        app_engine_http_request = task['app_engine_http_request']
        url = app_engine_http_request['relative_uri']
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
        self._queue.add_task(final_task)

        response = TaskResponse("Fake gcloud task", final_task)
        return response


class TaskResponse(NamedTuple):
    """
    Descriptor of the response
    """
    name: str
    task: dict


class GcloudFakeQueuePuller:
    """
    Simple puller class
    """

    def __init__(self, queue):
        """
        Create a puller that takes data from the queue and feed the processor.
        :param queue:
        """
        self._worker = None
        self._queue = queue

    def _work(self):
        """
        Internal worker that takes from the queue and process the value.
        It stops if a None message is found.
        :return:
        """
        while True:
            request = self._queue.get()
            if request.data is None:
                return
            if 'call' not in request.data:
                return
            if 'url' not in request.data:
                return
            call = request.data['call']
            url = request.data['url']
            args = request.data['args']
            # call("http://localhost:8080" + url, **args)

    def start(self):
        """
        Start the processing if it is not running
        """
        if self._worker is not None:
            return
        self._worker = threading.Thread(target=self._work)
        self._worker.start()

    def stop(self):
        """
        Stop the processing - if is is running - using a poison message.
        The queued messages will be processed.
        """
        if self._worker is None:
            return
        self._queue.add_task(None)
        self._worker.join()
        self._worker = None
