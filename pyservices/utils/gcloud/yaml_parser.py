import yaml


class YamlParser:
    def __init__(self, file_name, data):
        self.yaml_file = file_name
        self.data = data

    def get_yaml_file(self):
        return self.yaml_file

    def convert_and_write(self):
        data = self.convert()
        self.write_cron_file(data)

    def convert(self):
        """ This method should convert data to yaml lines"""
        raise NotImplementedError("Please Implement this method")

    def write_cron_file(self, data):
        try:
            with open(self.get_yaml_file(), 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)
        except Exception as ex:
            print(ex)
