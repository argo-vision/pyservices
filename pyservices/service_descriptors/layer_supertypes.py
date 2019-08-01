import inspect

from pyservices.service_descriptors.interfaces import InterfaceBase


class Service:
    """ Base class used for implementing a service.
    """
    service_base_path = None

    def __init__(self):
        """ Initialize the service instance.

        """
        self.dependencies = {}
        self.interface_descriptors = self._initialize_descriptors()

    def _initialize_descriptors(self):
        """ Initialize the interface descriptors.

        This is done for let the interface know which Service instance it is related
        to.

        Returns:
            A list of tuples of the descriptors initialized.
        """

        if_descriptors = inspect.getmembers(
            self, lambda m: inspect.isclass(m) and issubclass(m, InterfaceBase))
        return tuple([if_desc[1](self) for if_desc in if_descriptors])

    def add_connector(self, dependent_service_name, connector):
        self.dependencies[dependent_service_name] = connector
