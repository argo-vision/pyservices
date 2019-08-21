import logging
import threading

from pyservices.service_descriptors.layer_supertypes import ServiceOperationReference

logger = logging.getLogger(__package__)


class Puller:
    """
    Simple puller class
    """

    def __init__(self, queue):
        """
        Create a puller that takes data from the queue and feed the processor.
        :param queue:
        :param processor:
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
            task = self._queue.get()
            if not self._is_valid_task(task):
                return
            self._queue.set_to_processing()
            Puller._execute_task(task)
            self._queue.set_to_not_processing()

    @staticmethod
    def _is_valid_task(task):
        return task.data is not None

    @staticmethod
    def _execute_task(task):
        call = ServiceOperationReference(**task.data['reference'])
        data = task.data['data']
        params = {'args': {}, 'kwargs': data}
        call(params)

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
        self._queue.quit()
        self._worker.join()
        self._worker = None


