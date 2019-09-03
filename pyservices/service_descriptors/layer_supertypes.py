import inspect

from pyservices.service_descriptors.interfaces import HTTPInterface


class Service:
    """ Base class used for implementing a service.
    """
    service_base_path = None
    _module_prefix = 'services'

    def __init__(self, ctx):
        """ Initialize the service instance.

        """
        if hasattr(self, '__annotations__'):
            for k, v in self.__annotations__.items():
                if Service._skip_loading(v):
                    continue
                name = Service._create_name(v)
                component = ctx.get_component(name)
                setattr(self, k, component)

        self.interface_descriptors = self._initialize_descriptors()

    def start(self):
        for intf in self.interface_descriptors:
            intf.start()

    def stop(self):
        for intf in self.interface_descriptors:
            intf.stop()

    @classmethod
    def dependencies(cls):
        name = ["pyservices.service_descriptors.WSGIAppWrapper"]
        if hasattr(cls, '__annotations__'):
            for k, v in cls.__annotations__.items():
                if Service._skip_loading(v):
                    continue
                name.append(Service._create_name(v))
        return name

    @staticmethod
    def _skip_loading(v):
        return False

    @staticmethod
    def _create_name(v):
        if issubclass(v,Service):
            return '.'.join(v.__module__.split('.')[:-1])
        else:
            return v.__module__

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


class ServiceOperationReference:
    def __init__(self, service_name, interface_name, method_name):
        from pyservices.context import context
        self.ctx = context.context
        self.service = self.get_service(service_name)
        self.interface = self.get_interface(interface_name)
        self.method = self.get_method(method_name)

    def get_service(self, service_name):
        keyword_service_name = Service._module_prefix + "." + service_name
        return self.ctx.get_component(keyword_service_name.lower())

    def get_interface(self, interface_name):
        for s in self.service:
            if hasattr(s._request_handler, 'instance'):
                instance = s._request_handler.instance  # FIXME: this will change
                if instance.__class__.__name__.lower() == interface_name.lower():
                    return instance
        raise Exception()

    def get_method(self, method_name):
        methods = inspect.getmembers(self.interface, lambda m: inspect.ismethod(m))
        for m in methods:
            if m[0] == method_name.lower():
                return m[1]
        raise Exception()

    def __call__(self, data):
        return self.method(**data)
