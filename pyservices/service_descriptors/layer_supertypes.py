import inspect

from pyservices.service_descriptors.generators import RemoteServiceConnector
from pyservices.service_descriptors.interfaces import InterfaceBase, \
    HTTPInterface


class Service:
    """ Base class used for implementing a service.
    """
    service_base_path = None

    def __init__(self, config):
        """ Initialize the service instance.

        Attributes:
            config (dict): The configuration of the service.
        """
        self.config = config
        self.dependencies = {}
        self.interface_descriptors = self._initialize_descriptors()
        self.location = STUFF  # TODO from config

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

    @classmethod
    def get_interfaces(cls):
        ifaces = inspect.getmembers(
            cls, lambda i: inspect.isclass(i) and issubclass(i, HTTPInterface))
        return [iface[1] for iface in ifaces]

    def add_connector(self, connector):
        self.dependencies[connector.service_name] = connector

    def get_service_connector(self, remote):
        """ TODO remote is None if the connector is local
        """
        if remote:
            # It's non local
            return RemoteServiceConnector(self)
        else:
            # It's local
            return LocalServiceConnector(self)
