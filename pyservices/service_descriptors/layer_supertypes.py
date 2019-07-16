import inspect

import pyservices as ps
from pyservices.service_descriptors.interfaces import RestResourceInterface, InterfaceBase, HTTPInterface
from pyservices.service_descriptors.frameworks import get_framework_api
from wsgiref import simple_server
from threading import Thread


class Service:
    """ Base class used for implementing a service.
    """
    service_base_path = None

    def __init__(self, config: dict = None):
        """ Initialize the service instance.

        Attributes:
            config (dict): The configuration of the service.
        """
        self.config = config
        Service.service_base_path = Service.service_base_path or config['service_base_path']
        if not Service.service_base_path:
            raise Exception  # TODO must define service base path

        self.interface_descriptors = self._initialize_descriptors()
        self.thread = None
        self.httpd = None

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


    # TODO extend to other type of Interfaces
    @classmethod
    def get_rest_resources_meta_models(cls):
        """ Class method used to obtain the RestResources used

        Returns:
            (list) The list of the RestResources of the Service describer by
                the class.
        """
        resources = [m[1] for m in inspect.getmembers(
            cls, lambda m: inspect.isclass(m) and issubclass(m, RestResourceInterface))]
        return {res._get_endpoint_name(): res.meta_model for res in resources}

    """ Starts the service: TODO
    - Read configuration
    - Exposes interfaces
    - (TODO for each dependent service, initialize interfaces client)
    """
    def start(self):
        address = self.config.get('address')
        port = self.config.get('port')
        api = get_framework_api(self, self.config['framework'])
        # get WSGI app
        app = api.initialize_application()
        # TODO simple_server is temporary
        self.httpd = simple_server.make_server(address, int(port), app, handler_class=Handler)
        ps.log.info(f'Serving {self.service_base_path} on {address} port {port}')
        self.thread = Thread(target=self.httpd.serve_forever)
        self.thread.start()

    """ TODO temporary"""
    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()


# TODO simple_server is temporary
class Handler(simple_server.WSGIRequestHandler):
    """ Wraps the default handler to avoid stderr logs
    """

    def log_message(self, *arg, **kwargs):
        ps.log.info("received {}: result {}".format(*arg[1:3]))

    def get_stderr(self, *arg, **kwargs):
        pass
