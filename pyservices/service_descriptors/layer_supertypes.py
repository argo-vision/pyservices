import inspect

from pyservices.service_descriptors.interfaces import HTTPInterface


class Service:
    """ Base class used for implementing a service.
    """
    service_base_path = None
    _module_prefix = 'services'

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

    @staticmethod
    def get_method_reference(service_name, interface_name, method_name):
        return ServiceOperationReference(service_name, interface_name, method_name)


class ServiceOperationReference:
    def __init__(self, service_name, interface_name, method_name):
        from pyservices.context import context
        self.ctx = context.context
        self.service = self.get_service(service_name)
        self.interface = self.get_interface(interface_name)
        self.method = self.get_method(method_name)

    def get_service(self, service_name):
        keyword_service_name = Service._module_prefix + "." + service_name
        return self.ctx.get_component(keyword_service_name)

    def get_interface(self, interface_name):
        for s in self.service:
            instance = s._request_handler.instance  # FIXME: this will change
            if instance.__class__.__name__ == interface_name:
                return instance
        raise Exception()

    def get_method(self, method_name):
        methods = inspect.getmembers(self.interface, lambda m: inspect.ismethod(m))
        for m in methods:
            if m[0] == method_name:
                return m[1]
        raise Exception()

    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)
