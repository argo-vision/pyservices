import unittest

from pyservices.data_descriptors.entity_codecs import *
from pyservices.utilities.exceptions import MetaTypeException
from test.data_descriptors.meta_models import *


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.person_dict = {
            'person_name': 'my_person_name',
            'last_access': datetime.now(),
            'credentials': {
                'password': 'my_password',
                'vocal_features': 'my_vocal_features'
            },
            'address': {
                'city': 'my_city',
                'postal_code': 'my_postal_code'
            }
        }
        self.person_ma_repr = {
            'addresses': [
                {'city': 'MyCity', 'postal_code': '44444'},
                {'city': 'MySecondCity', 'postal_code': '53102'}],
            'last_access': datetime(2019, 3, 9, 0, 33, 6, 386788),
            'person_name': 'MyPersonname'}

    def test_instance_attributes(self):
        attributes = instance_attributes(Person())
        self.assertListEqual(attributes, ['address', 'credentials',
                                          'last_access', 'person_name'])

    def test_dict_repr_to_instance(self):
        person_instance = dict_repr_to_instance(
            self.person_dict, PersonMM)
        self.assertIsInstance(person_instance, Person)
        self.assertIsInstance(person_instance.credentials, Credentials)
        self.assertIsInstance(person_instance.address, Address)
        self.assertEqual(person_instance.person_name, 'my_person_name')
        self.assertEqual(person_instance.credentials.password, 'my_password')
        self.assertEqual(person_instance.address.city, 'my_city')

    def test_dict_repr_to_instance_sequence_field(self):
        instance = dict_repr_to_instance(
            self.person_ma_repr, PersonMultipleAddressMM)
        self.assertEqual(instance.addresses[0].city, 'MyCity')
        self.assertEqual(instance.addresses[1].postal_code, '53102')

    def test_dict_repr_to_instance_bad_usage(self):
        bad_dict = {
            'person_name': 'my_person_name',
            'now_a_valid_key': {}
        }
        self.assertRaises(MetaTypeException,
                          dict_repr_to_instance,
                          bad_dict, PersonMM)

    def test_instance_to_dict_repr(self):
        person_dict = instance_to_dict_repr(
            Person('my_person_name', datetime.now(),
                   Credentials('my_password', 'secret'), addresses[0]))
        self.assertEqual(person_dict['credentials']['password'],
                         'my_password')
        self.assertEqual(person_dict['address']['city'],
                         'MyCity')
        self.assertEqual(person_dict['person_name'],
                         'my_person_name')

    def test_instance_to_dict_repr_sequence_field(self):
        instance_dict = instance_to_dict_repr(person_ma)
        self.assertEqual(instance_dict['addresses'][0]['city'], 'MyCity')
        self.assertEqual(instance_dict['addresses'][1]['postal_code'], '53102')

    def test_instance_to_dict_repr_conditional_field(self):
        try:
            fa_repr = instance_to_dict_repr(
                first_type_account)
            sa_repr = instance_to_dict_repr(
                second_type_account)
        except Exception as e:
            self.fail(e)
        self.assertEqual(fa_repr['connector']['app_id'], 'my_app_id')
        self.assertEqual(sa_repr['connector']['access']['secret'],
                         'my_secret')

    def test_dict_repr_to_instance_conditional_field(self):
        first_account_repr = {
            "connector": {
                "app_id": "my_app_id",
                "secret": "my_secret",
                "token": "my_token"},
            "connector_type": "first",
            "email": "my@email.com"}

        second_account_repr = {
            "connector": {
                "access": {
                    "secret": "my_secret",
                    "service": "my_service"},
                "token": "token"},
            "connector_type": "second",
            "email": "my@email.com"}

        try:
            fta = dict_repr_to_instance(first_account_repr, AccountConnectorsMM)
            sta = dict_repr_to_instance(second_account_repr,
                                        AccountConnectorsMM)
        except Exception as e:
            self.fail(e)
        self.assertEqual(fta.connector.app_id,
                         first_type_account.connector.app_id)
        self.assertEqual(sta.connector.access.service,
                         second_type_account.connector.access.service)

    def test_dict_repr_to_instance_dict_field(self):
        try:
            p = Palette('my_palette', {
                'red': '#ff0000',
                'green': '#00ff00',
                'blue': '#0000ff'})
        except Exception as e:
            self.fail(e)

        repr_v = instance_to_dict_repr(p)
        self.assertDictEqual(obj_repr, repr_v)

    def test_instance_to_dict_repr_dict_field(self):
        instance = dict_repr_to_instance(obj_repr, PaletteMM)
        self.assertEqual(instance.colors['red'], '#ff0000')


class TestJSON(unittest.TestCase):

    def setUp(self):
        self.person_instance = Person('my_person_name',
                                      '2019-02-21T16:03:52.147559',
                                      Credentials('super', 'secrets'),
                                      addresses[0])
        self.person_json = '{"address": {"city": "MyCity", "postal_code": "44444"}, "credentials": {"password": "super", "vocal_features": "secrets"}, "last_access": "2019-02-21 16:03:52.147559", "person_name": "my_person_name"}'
        self.codec = JSON

    def test_decode(self):
        instance_json = self.codec.encode(self.person_instance)
        self.assertEqual(instance_json, self.person_json)

    def test_encode(self):
        person = self.codec.decode(self.person_json, PersonMM)
        self.assertEqual(person.address.city, 'MyCity')


if __name__ == '__main__':
    unittest.main()
