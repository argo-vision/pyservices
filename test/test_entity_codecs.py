import unittest

from datetime import datetime

import pyservices as ps
from pyservices.data_descriptors import MetaModel, StringField, DateTimeField, \
    ComposedField, SequenceField, ConditionalField, DictField


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

    def test_dict_repr_to_instance(self):
        user_instance = ps.entity_codecs.dict_repr_to_instance(
            self.user_dict, self.user_meta_model)
        self.assertIsInstance(user_instance, self.user_meta_model.get_class())
        self.assertIsInstance(user_instance.credentials,
                              self.user_meta_model.fields[2].get_class())
        self.assertIsInstance(user_instance.address,
                              self.address_meta_model.get_class())
        self.assertEqual(user_instance.username, 'my_username')
        self.assertEqual(user_instance.credentials.password, 'my_password')
        self.assertEqual(user_instance.address.city, 'my_city')

    def test_dict_repr_to_instance_sequence_field(self):
        instance = ps.entity_codecs.dict_repr_to_instance(
            self.user_ma_repr, self.user_multiple_addresses_mm)
        self.assertEqual(instance.addresses[0].city, 'MyCity')
        self.assertEqual(instance.addresses[1].postal_code, '53102')

    def test_dict_repr_to_instance_bad_usage(self):
        bad_dict = {
            'username': 'my_username',
            'now_a_valid_key': {}
        }
        self.assertRaises(TypeError, ps.entity_codecs.dict_repr_to_instance,
                          bad_dict, self.user_meta_model)

    def test_instance_to_dict_repr(self):
        user_dict = ps.entity_codecs.instance_to_dict_repr(self.user_instance)
        self.assertEqual(user_dict['credentials']['password'],
                         'my_password')
        self.assertEqual(user_dict['address']['city'],
                         'my_city')
        self.assertEqual(user_dict['username'],
                         'my_username')

    def test_instance_to_dict_repr_sequence_field(self):
        instance_dict = ps.entity_codecs.instance_to_dict_repr(self.user_ma)
        self.assertEqual(instance_dict['addresses'][0]['city'], 'MyCity')
        self.assertEqual(instance_dict['addresses'][1]['postal_code'], '53102')

    def test_instance_to_dict_repr_conditional_field(self):
        access = ComposedField('access', StringField('secret'),
                               StringField('service'))
        first_connector = MetaModel('First_connector', StringField('app_id'),
                                    StringField('token'), StringField('secret'))
        second_connector = MetaModel('Second_connector', StringField('token'),
                                     access)
        connector = ConditionalField('connector', {
            'first': first_connector,
            'second': second_connector}, evaluation_field_name='connector_type')

        account = MetaModel('Account', StringField('email'),
                            connector, StringField('connector_type'))

        Access = access.meta_model.get_class()
        Account = account.get_class()
        first_conn_auth = first_connector.get_class()('my_app_id',
                                                      'my_token',
                                                      'my_secret')

        second_conn_auth = second_connector.get_class()('token',
                                                        Access('my_secret',
                                                               'my_service'))

        first_type_account = Account('my@email.com', first_conn_auth,
                                     connector_type='first')

        second_type_account = Account('my@email.com', second_conn_auth,
                                      connector_type='second')

        try:
            fa_repr = ps.entity_codecs.instance_to_dict_repr(
                first_type_account)
            sa_repr = ps.entity_codecs.instance_to_dict_repr(
                second_type_account)
        except Exception as e:
            self.fail(e)
        self.assertEqual(fa_repr['connector']['app_id'], 'my_app_id')
        self.assertEqual(sa_repr['connector']['access']['secret'],
                         'my_secret')

    def test_dict_repr_to_instance_conditional_field(self):
        access = ComposedField('access', StringField('secret'),
                               StringField('service'))
        first_connector = MetaModel('First_connector', StringField('app_id'),
                                    StringField('token'), StringField('secret'))
        second_connector = MetaModel('Second_connector', StringField('token'),
                                     access)
        connector = ConditionalField('connector', {
            'first': first_connector,
            'second': second_connector}, evaluation_field_name='connector_type')

        account = MetaModel('Account', StringField('email'),
                            connector, StringField('connector_type'))

        Access = access.meta_model.get_class()
        Account = account.get_class()
        first_conn_auth = first_connector.get_class()('my_app_id',
                                                      'my_token',
                                                      'my_secret')

        second_conn_auth = second_connector.get_class()('token',
                                                        Access('my_secret',
                                                               'my_service'))

        first_type_account = Account('my@email.com', first_conn_auth,
                                     connector_type='first')

        second_type_account = Account('my@email.com', second_conn_auth,
                                      connector_type='second')

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
            fta = ps.entity_codecs.dict_repr_to_instance(first_account_repr,
                                                    account)
            sta = ps.entity_codecs.dict_repr_to_instance(second_account_repr,
                                                    account)
        except Exception as e:
            self.fail(e)
        self.assertEqual(fta.connector.app_id,
                         first_type_account.connector.app_id)
        self.assertEqual(sta.connector.access.service,
                         second_type_account.connector.access.service)

    def test_dict_repr_to_instance_dict_field(self):
        color_fields = DictField('colors')
        palette_meta_model = MetaModel('Palette', StringField('name'),
                                       color_fields)
        Palette = palette_meta_model.get_class()
        obj_repr = {
            'colors': {
                'red': '#ff0000',
                'green': '#00ff00',
                'blue': '#0000ff' },
            'name': 'my_palette'}

        try:
            p = Palette('my_palette', {
                'red': '#ff0000',
                'green': '#00ff00',
                'blue': '#0000ff'})
        except Exception as e:
            self.fail(e)

        repr_v = ps.entity_codecs.instance_to_dict_repr(p)
        self.assertDictEqual(obj_repr, repr_v)

    def test_instance_to_dict_repr_dict_field(self):
        color_fields = DictField('colors')
        palette_meta_model = MetaModel('Palette', StringField('name'),
                                       color_fields)
        obj_repr = {
            'colors': {
                'red': '#ff0000',
                'green': '#00ff00',
                'blue': '#0000ff'},
            'name': 'my_palette'}
        instace = ps.entity_codecs.dict_repr_to_instance(obj_repr, palette_meta_model)
        self.assertEqual(instace.colors['red'], '#ff0000')


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
        user = self.codec.decode(self.user_json, self.user_meta_model)
        self.assertEqual(user.address.city, 'my_city')


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
