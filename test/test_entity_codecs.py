import unittest

from datetime import datetime

import pyservices as ps
from pyservices.data_descriptors import MetaModel, StringField, DateTimeField, \
    ComposedField, SequenceField


# TODO refactor
class TestUtils(unittest.TestCase):

    def setUp(self):
        self.user_instance = User('my_username', datetime.now(),
                                  'my_password', 'myVocalFeatures',
                                  'my_city', 'my_postalCode')
        self.users = [self.user_instance for _ in range(5)]

        self.user_dict = {
            'username': 'my_username',
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
        MetaModel.modelClasses = dict()
        self.address_meta_model = MetaModel(
            'Address',
            StringField('city'),
            StringField('postal_code'))
        self.user_meta_model = MetaModel(
            'User',
            StringField('username'),
            DateTimeField('last_access'),
            ComposedField('credentials',
                          StringField('password'),
                          StringField('vocal_features')),
            self.address_meta_model())
        self.user_multiple_addresses_mm = MetaModel(
            'UserMA', StringField('username'),
            DateTimeField('last_access'),
            SequenceField('addresses', data_type=self.address_meta_model())
        )

        self.addresses = [
            self.address_meta_model.get_class()('MyCity', '44444'),
            self.address_meta_model.get_class()('MySecondCity', '53102')]

        self.user_ma = self.user_multiple_addresses_mm.get_class()(
            'MyUsername', datetime.now(), self.addresses
        )
        self.user_ma_repr = {
            'addresses': [
                {'city': 'MyCity', 'postal_code': '44444'},
                {'city': 'MySecondCity', 'postal_code': '53102'}],
            'last_access': datetime(2019, 3, 9, 0, 33, 6, 386788),
            'username': 'MyUsername'}

    def test_get(self):
        username = ps.entity_codecs.get(self.user_instance, 'username')
        credentials = ps.entity_codecs.get(self.user_instance, 'credentials')
        self.assertEqual(username, 'my_username')
        self.assertEqual(credentials, self.user_instance.credentials)

    def test_instance_attributes(self):
        attributes = ps.entity_codecs.instance_attributes(self.user_instance)
        self.assertListEqual(attributes, ['address', 'credentials',
                                          'last_access', 'username'])

    def test_repr_to_instance(self):
        user_instance = ps.entity_codecs.repr_to_instance(
            self.user_dict, self.user_meta_model)
        self.assertIsInstance(user_instance, self.user_meta_model.get_class())
        self.assertIsInstance(user_instance.credentials,
                              self.user_meta_model.fields[2].get_class())
        self.assertIsInstance(user_instance.address,
                              self.address_meta_model.get_class())
        self.assertEqual(user_instance.username, 'my_username')
        self.assertEqual(user_instance.credentials.password, 'my_password')
        self.assertEqual(user_instance.address.city, 'my_city')

    def test_repr_to_instance_sequence_field(self):
        instance = ps.entity_codecs.repr_to_instance(
            self.user_ma_repr, self.user_multiple_addresses_mm)
        self.assertEqual(instance.addresses[0].city, 'MyCity')
        self.assertEqual(instance.addresses[1].postal_code, '53102')

    def test_repr_to_instance_bad_usage(self):
        bad_dict = {
            'username': 'my_username',
            'now_a_valid_key': {}
        }
        self.assertRaises(TypeError, ps.entity_codecs.repr_to_instance,
                          bad_dict, self.user_meta_model)

    def test_instance_to_repr(self):
        user_dict = ps.entity_codecs.instance_to_repr(self.user_instance)
        self.assertEqual(user_dict['credentials']['password'],
                         'my_password')
        self.assertEqual(user_dict['address']['city'],
                         'my_city')
        self.assertEqual(user_dict['username'],
                         'my_username')

    def test_instance_to_repr_sequence_field(self):
        instance_dict = ps.entity_codecs.instance_to_repr(self.user_ma)
        self.assertEqual(instance_dict['addresses'][0]['city'], 'MyCity')
        self.assertEqual(instance_dict['addresses'][1]['postal_code'], '53102')


class TestJSON(unittest.TestCase):

    def setUp(self):
        self.user_instance = User('my_username', '2019-02-21T16:03:52.147559',
                                  'my_password', 'myVocalFeatures',
                                  'my_city', 'my_postalCode')
        self.user_json = '{"address": {"city": "my_city", "postal_code": "my_' \
                         'postalCode"}, "credentials": {"password": "my_passw' \
                         'ord", "vocal_features": "myVocalFeatures"}, "last_a' \
                         'ccess": "2019-02-21T16:03:52.147559", "username": "' \
                         'my_username"}'
        self.codec = ps.entity_codecs.JSON()

        MetaModel.modelClasses = dict()
        self.address_meta_model = MetaModel(
            'Address',
            StringField('city'),
            StringField('postal_code'))
        self.user_meta_model = MetaModel(
            'User',
            StringField('username'),
            DateTimeField('last_access'),
            ComposedField('credentials',
                          StringField('password'),
                          StringField('vocal_features')),
            self.address_meta_model())

    def test_decode(self):
        instance_json = self.codec.encode(self.user_instance)
        self.assertEqual(instance_json, self.user_json)

    def test_encode(self):
        self.codec.decode(self.user_json, self.user_meta_model)


class Address:
    def __init__(self, city, postal_code):
        self.city = city
        self.postal_code = postal_code


class Credentials:
    def __init__(self, password, vocal_features):
        self.password = password
        self.vocal_features = vocal_features


class User:
    def __init__(self, username, last_access, password,
                 vocal_features, city, postal_code):
        self.username = username
        self.last_access = last_access
        self.credentials = Credentials(password, vocal_features)
        self.address = Address(city, postal_code)


if __name__ == '__main__':
    unittest.main()
