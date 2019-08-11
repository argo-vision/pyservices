# from pyservices.utils.gcloud.exceptions import GcloudEnvironmentException
from pyservices.utils.gcloud import get_project_id, check_if_gcloud

COMPONENT_KEY = __name__
COMPONENT_DEPENDENCIES = []


# TODO keep url composer with static methods?
class DefaultUrlComposer:
    """
    Class url composer
    """

    def __init__(self, micro_service_configuration):
        self._ms_config = micro_service_configuration

    def get_https_url(self, service):
        return _get_url('https', self._ms_config.host_of(service))

    def get_http_url(self, service):
        return _get_url('http', self._ms_config.host_of(service))


# TODO are http/https host the same?
class GCloudUrlComposer(DefaultUrlComposer):
    """
    Class url composer for GCloud service
    """
    ending = 'com'

    def get_https_url(self, service):
        return _get_url('https', self._get_host(service))

    def get_http_url(self, service):
        return _get_url('http', self._get_host(service))

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
