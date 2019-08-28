from urllib.parse import urlparse
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


