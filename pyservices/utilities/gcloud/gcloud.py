from urllib.parse import urlparse

from .exceptions import GcloudEnvironmentException
from .gcloud_utilities import check_if_gcloud, get_project_id
from .url_composer import DefaultUrlComposer
from .yaml_parser import YamlParser



class GcloudCronParser(YamlParser):
    def __init__(self, timers):
        super().__init__("cron.yaml", timers)

    def convert(self):
        items = []
        for cron_item in self.data:
            parsed = self.convert_cron_item(cron_item)
            items.append(parsed)

        result = {
            "cron": items
        }
        return result

    def convert_cron_item(self, cron_item):
        result = {
            "description": cron_item['name'],
            "url": self.extract_local_url(cron_item['url']),
            "schedule": self.extract_scheduling(cron_item['interval'])

        }
        return result

    @staticmethod
    def extract_local_url(url):
        parsed = urlparse(url)
        return parsed.path

    @staticmethod
    def extract_scheduling(interval):
        return "every {} minutes".format(int((interval + 60) / 60))


class GcloudUrlComposer(DefaultUrlComposer):
    """
    Class url composer for service_utils service
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
