import inspect

from pyservices.service_descriptors.interfaces import HTTPInterface


class Service:
    """ Base class used for implementing a service.
    """
    service_base_path = None

    def __init__(self):
        """ Initialize the service instance.

        """
        self.interface_descriptors = self._initialize_descriptors()

    def _initialize_descriptors(self):
        """ Initialize the interface descriptors.

        This is done for let the interface know which Service instance it is related
        to.

        Returns:
            A list of tuples of the descriptors initialized.
        """

        interfaces = self.interfaces()
        return tuple(if_desc(self) for if_desc in interfaces)

    @classmethod
    def interfaces(cls):
        return [cls_attribute for cls_attribute in cls.__dict__.values()
                if inspect.isclass(cls_attribute)
                and issubclass(cls_attribute, HTTPInterface)]
