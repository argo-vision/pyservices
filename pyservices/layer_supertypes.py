import inspect

from pyservices.interfaces import RestResource, InterfaceBase
from pyservices.db_connectors import DBConnector


# TODO docs
# TODO context pattern!!?
class ServiceContext:

    # TODO dependencies, injector pattern??
    def __init__(self, db_connector: DBConnector = None,
                 # dependencies: Mapping[str, Service] = None
                 ):
        self.db_connector = db_connector
        # self.dependencies = dependencies


# TODO docs
class Service:
    """ Base class used for implementing a service.
    """
    def __init__(self, config: dict = None, db_connector: DBConnector = None):
        """ Initialize the service instance.

        Attributes:
            config (dict): The configuration of the service.
            TODO
            TODO
        """
        self.context = ServiceContext(db_connector=db_connector)
        self.config = config

        # TODO
        # self._interfaces = {}
        self.interface_descriptors = self._initialize_descriptors()

    def _initialize_descriptors(self):
        """ Initialize the interface descriptors.

        This is done for let the iface know which service is it related to.
        """
        # this returns a list of tuples
        iface_descriptors = inspect.getmembers(
            self, lambda m: inspect.isclass(m) and issubclass(m, InterfaceBase))
        return [iface_desc[1](self) for iface_desc in iface_descriptors]

    def get_rest_resources(self):
        rest_resources = [iface_desc
                          for iface_desc in self.interface_descriptors
                          if isinstance(iface_desc, RestResource)]
        return {res.resource_path or f'{res.meta_model.name.lower()}s': res
                for res in rest_resources}

    def get_service_path(self):
        # TODO put default behaviour elsewhere #configurations
        port = self.config.get('port') or '7890'
        address = self.config.get('address') or 'localhost'
        service_base_path = self.config.get('service_base_path')
        return f'http://{address}:{port}/{service_base_path}'
