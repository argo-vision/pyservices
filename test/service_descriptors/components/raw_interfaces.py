from pyservices.data_descriptors.fields import IntegerField
from pyservices.data_descriptors.meta_model import MetaModel
from pyservices.service_descriptors.interfaces import RPCInterface, \
    RestResourceInterface
from pyservices.data_descriptors.entity_codecs import JSON


class TestRPCInterface(RPCInterface):

    def method(self, param1):
        pass


my_mm = MetaModel('MyTestData', IntegerField('id'), primary_key_name='id')


class TestRestInterface(RestResourceInterface):
    meta_model = my_mm
    codec = JSON

    def collect(self):
        pass

    def detail(self, res_id):
        pass


