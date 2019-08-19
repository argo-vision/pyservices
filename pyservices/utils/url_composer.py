# from pyservices.utils.gcloud.exceptions import GcloudEnvironmentException
from pyservices.utils.gcloud import get_project_id, check_if_gcloud
import pyservices.context.microservice_utils as config_utils

COMPONENT_KEY = __name__
COMPONENT_DEPENDENCIES = []


# TODO keep url composer with static methods?
class DefaultUrlComposer:
    """
    Class url composer
    """

    @staticmethod
    def get_https_url(microservice):
        return _get_url('https', config_utils.host(microservice))

    @staticmethod
    def get_http_url(microservice):
        return _get_url('http', config_utils.host(microservice))


# TODO are http/https host the same?
class GCloudUrlComposer(DefaultUrlComposer):
    """
    Class url composer for GCloud service
    """
    ending = 'com'

    @staticmethod
    def get_https_url(service):
        return _get_url('https', GCloudUrlComposer._get_host(service))

    @staticmethod
    def get_http_url(service):
        return _get_url('http', GCloudUrlComposer._get_host(service))

    @classmethod
    def _get_host(cls, service):
        from pyservices.context.dependencies import get_service_class
        # TODO Assume that service_name is service_base_path?
        service_name = get_service_class(service).service_base_path
        project_id = get_project_id()  # TODO what if
        # TODO I have to communicate with services in other projects
        # TODO Possible solution: add project_id on configuration
        return f'{service_name}.{project_id}.{cls.ending}'


def _get_url(protocol, host):
    """
    Produces the url of a given service

    Args:
        protocol (str): The protocol to prepend in the url
        host (str): Host of the url (e.g. address:port)

    Returns:
        The url
    """
    return f'{protocol}://{host}'
