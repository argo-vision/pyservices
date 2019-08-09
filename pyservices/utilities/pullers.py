import logging
import threading

logger = logging.getLogger(__package__)


class Puller:
    """
    Simple puller class
    """

    def __init__(self, queue, processor):
        """
        Create a puller that takes data from the queue and feed the processor.
        :param queue:
        :param processor:
        """
        self._worker = None
        self._processor = processor
        self._queue = queue

    def _work(self):
        """
        Internal worker that takes from the queue and process the value.
        It stops if a None message is found.
        :return:
        """
        while True:
            val = self._queue.get()
            if val.data is None:
                return
            self._processor.feed([val])

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
        self._queue.put(None)
        self._worker.join()
        self._worker = None


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
            if 'call' not in request.data:
                return
            if 'url' not in request.data:
                return
            call = request.data['call']
            url = request.data['url']
            args = request.data['args']
            call(url, **args)

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
        self._queue.put(None)
        self._worker.join()
        self._worker = None