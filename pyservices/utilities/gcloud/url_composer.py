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


def build_localhost_url_composer(port=80):
    """
    Construct a DefaultUrlComposer object for localhost. It's preferable over __init__ class method

    :param port: port of the service
    :rtype: DefaultUrlComposer
    """

    composer = DefaultUrlComposer(port)
    return composer

