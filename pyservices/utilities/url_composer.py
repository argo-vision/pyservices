from pyservices.utilities.gcloud.exceptions import GcloudEnvironmentException
from pyservices.utilities.gcloud.gcloud import get_project_id, check_if_gcloud, get_current_service_name
from pyservices.context import Context
from tools.configuration.config_generator import config_generator

COMPONENT_KEY = __name__
COMPONENT_DEPENDENCIES = []


class DefaultUrlComposer:
    """
    Class url composer
    """

    def __init__(self, port):

        args = ["localhost", port]

        self._compose_http_host(args)
        self._compose_https_host(args)

    def _compose_http_host(self, args):
        self._http_host = "{}:{}".format(args[0], args[1])

    def _compose_https_host(self, args):
        self._https_host = "{}:{}".format(args[0], args[1])

    def get_https_url(self, path="/"):
        """
        Compose Url for the service
        :param path : path appended to service url
        :return url : https service url
        """

        protocol = "https"
        return _get_url(protocol, self._https_host, path)

    def get_http_url(self, path="/"):
        """
        Compose Url for the service
        :param path : path appended to service url
        :return url : http service url
        """
        protocol = "http"
        return _get_url(protocol, self._http_host, path)


class GcloudUrlComposer(DefaultUrlComposer):
    """
    Class url composer for gcloud service
    """

    def __init__(self, service_name, project_id, base_path="/"):
        """
        Compose Url for the service
        :param service_name : name of the service
        :param project_id : project id
        """

        self.ending = "com"
        args = [project_id, service_name, base_path]
        super().__init__(args)

    def _compose_http_host(self, args):
        _project_id = args[0]
        _service_name = args[1]
        _base_path = args[2]
        self._http_host = "{}.{}.{}".format(_service_name, _project_id, self.ending, _base_path)

    def _compose_https_host(self, args):
        _project_id = args[0]
        _service_name = args[1]
        _base_path = args[2]
        self._https_host = "{}-dot-{}.{}".format(_service_name, _project_id, self.ending, _base_path)


def build_localhost_url_composer(port=80):
    """
    Construct a DefaultUrlComposer object for localhost. It's preferable over __init__ class method

    :param port: port of the service
    :rtype: DefaultUrlComposer
    """

    composer = DefaultUrlComposer(port)
    return composer


def build_gcloud_url_composer_from_environment(service_name):
    """
    Construct a UrlComposer object for the specified service. It's preferable over __init__ class method

    :param service_name: name of the service. Can be different from the current service
    :rtype: GcloudUrlComposer
    """

    if check_if_gcloud():
        project_id = get_project_id()
        composer = GcloudUrlComposer(service_name, project_id)
        return composer
    else:
        raise GcloudEnvironmentException()


def _get_url(protocol, host, path):
    path = _refine_path(path)
    result = "{}://{}{}".format(protocol, host, path)
    return result


def _refine_path(path):
    if path[0] != "/":
        path = "/" + path
    if path[-1] == "/":
        path = path[0:-2]
    return path