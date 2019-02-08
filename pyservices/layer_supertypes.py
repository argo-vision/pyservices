import inspect

from pyservices.interfaces import RestResource, InterfaceBase
from pyservices.db_connectors import DBConnector


class ServiceContext:
    """ The context of the service.
    """
    def __init__(self, db_connector: DBConnector = None,
                 # dependencies: Mapping[str, Service] = None TODO
                 ):
        self.db_connector = db_connector
        # self.dependencies = dependencies


class Service:
    """ Base class used for implementing a service.
    """
    def __init__(self, config: dict = None, db_connector: DBConnector = None):
        """ Initialize the service instance.

        Attributes:
            config (dict): The configuration of the service.
            db_connector (DBConnector):
            TODO
        """
        self.context = ServiceContext(db_connector=db_connector)
        self.config = config

        self.interface_descriptors = self._initialize_descriptors()

    def _initialize_descriptors(self):
        """ Initialize the interface descriptors.

        This is done for let the iface know which Service instance it is related
        to.

        Returns:
            A list of tuples of the descriptors initialized.
        """

        iface_descriptors = inspect.getmembers(
            self, lambda m: inspect.isclass(m) and issubclass(m, InterfaceBase))
        return tuple([iface_desc[1](self) for iface_desc in iface_descriptors])

    @classmethod
    def get_rest_resources_meta_models(cls):
        """ Class method used to obtain the RestResources used

        Returns:
            (list) The list of the RestResources of the Service describer by
                the class.
        """
        resources = [m[1] for m in inspect.getmembers(
            cls, lambda m: inspect.isclass(m) and issubclass(m, RestResource))]
        return {res.get_resource_name(): res.meta_model for res in resources}

    def get_service_path(self):
        # TODO put default behaviour elsewhere (issue #7)
        port = self.config.get('port') or '7890'
        address = self.config.get('address') or 'localhost'
        service_base_path = self.config.get('service_base_path')
        return f'http://{address}:{port}/{service_base_path}'
