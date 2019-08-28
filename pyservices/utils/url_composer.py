from pyservices.utils.gcloud import check_if_gcloud, get_project_id, get_service_id
from pyservices.utils.gcloud.exceptions import GcloudEnvironmentException

COMPONENT_KEY = __name__
COMPONENT_DEPENDENCIES = []


# TODO keep url composer with static methods?
class DefaultUrlComposer:
    """
    Class url composer
    """

    @staticmethod
    def get_https_url(service):
        """
        Default url composer provide http url only

        """

        return DefaultUrlComposer.get_http_url(service)

    @staticmethod
    def get_http_url(service):
        return f'{DefaultUrlComposer._get_url("http", DefaultUrlComposer.get_host())}:' \
               f'{DefaultUrlComposer._get_current_port()}/{DefaultUrlComposer.get_base_route(service)}'

    @staticmethod
    def _get_current_port():
        from pyservices.context.microservice_utils import current_host
        current_host = current_host()
        return current_host.split(':')[1]

    @staticmethod
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

    @classmethod
    def get_host(cls):
        return 'localhost'

    @staticmethod
    def get_base_route(service):
        from pyservices.context.dependencies import get_service_class
        service_route = get_service_class(service).service_base_path
        return service_route


# TODO are http/https host the same?
class GCloudUrlComposer(DefaultUrlComposer):
    """
    Class url composer for GCloud service
    """
    ending = 'com'

    @staticmethod
    def get_https_url(service):
        return f'{DefaultUrlComposer._get_url("https", GCloudUrlComposer.get_host())}' \
               f'/{GCloudUrlComposer.get_base_route(service)}'

    @staticmethod
    def get_base_route(service):
        from pyservices.context.dependencies import get_service_class
        service_route = get_service_class(service).service_base_path
        return service_route

    @classmethod
    def get_host(cls):
        # TODO Assume that service_name is service_base_path?
        service_name = get_service_id()
        project_id = get_project_id()  # TODO what if
        # TODO I have to communicate with services in other projects
        # TODO Possible solution: add project_id on configuration
        return f'{service_name}-dot-{project_id}.appspot.{cls.ending}'


def build_gcloud_url_composer_from_environment():
    """
    Construct a UrlComposer object for the specified service. It's preferable over __init__ class method

    :param service_name: name of the service. Can be different from the current service
    :rtype: GcloudUrlComposer
    """

    if check_if_gcloud():
        composer = GCloudUrlComposer()
        return composer
    else:
        raise GcloudEnvironmentException()


def build_localhost_url_composer():
    """
    Construct a UrlComposer object for the specified service. It's preferable over __init__ class method

    :param service_name: name of the service. Can be different from the current service
    :rtype: GcloudUrlComposer
    """

    return DefaultUrlComposer()
