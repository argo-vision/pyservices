import unittest

from datetime import datetime

import pyservices as ps
from pyservices.data_descriptors import MetaModel, StringField, DateTimeField, \
    ComposedField


# TODO case dict conventions and obj
# TODO check setup instance attrs name
#
class TestUtils(unittest.TestCase):

    def setUp(self):
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

        self.user_instance = User('my_username', datetime.now(),
                                  'my_password', 'myVocalFeatures',
                                  'my_city', 'my_postalCode')

        self.user_dict = {
            'username': 'my_username',
            'lastAccess': datetime.now(),
            'credentials': {
                'password': 'my_password',
                'vocalFeatures': 'my_vocal_features'
            },
            'address': {
                'city': 'my_city',
                'postalCode': 'my_postal_code'
            }

        }
        MetaModel.modelClasses = dict()
        self.address_meta_model = MetaModel(
            'Address',
            StringField('city'),
            StringField('postalCode'))
        self.user_meta_model = MetaModel(
            'User',
            StringField('username'),
            DateTimeField('lastAccess'),
            ComposedField('credentials',
                          StringField('password'),
                          StringField('vocalFeatures')),
            self.address_meta_model())

    def test_get(self):
        username = ps.entity_codecs.get(self.user_instance, 'username')
        credentials = ps.entity_codecs.get(self.user_instance, 'credentials')
        self.assertEqual(username, 'my_username')
        self.assertEqual(credentials, self.user_instance.credentials)

    def test_instance_attributes(self):
        attributes = ps.entity_codecs.instance_attributes(self.user_instance)
        self.assertListEqual(attributes, ['address', 'credentials',
                                          'last_access', 'username'])

    def test_dict_to_instance(self):
        user_instance = ps.entity_codecs.dict_to_instance(self.user_dict,
                                                          self.user_meta_model)
        self.assertIsInstance(user_instance, self.user_meta_model.get_class())
        self.assertIsInstance(user_instance.credentials,
                              self.user_meta_model.fields[2].get_class())
        self.assertIsInstance(user_instance.address,
                              self.address_meta_model.get_class())
        self.assertEqual(user_instance.username, 'my_username')
        self.assertEqual(user_instance.credentials.password, 'my_password')
        self.assertEqual(user_instance.address.city, 'my_city')

    def test_dict_to_instance_bad_usage(self):
        bad_dict = {
            'username': 'my_username',
            'now_a_valid_key': {}
        }
        self.assertRaises(TypeError, ps.entity_codecs.dict_to_instance,
                          bad_dict, self.user_meta_model)

    def test_instance_to_dict(self):
        user_dict = ps.entity_codecs.instance_to_dict(self.user_instance)
        self.assertEqual(user_dict['credentials']['password'],
                         'my_password')
        self.assertEqual(user_dict['address']['city'],
                         'my_city')
        self.assertEqual(user_dict['username'],
                         'my_username')


class TestJSON(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
