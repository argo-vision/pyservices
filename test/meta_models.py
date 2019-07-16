from datetime import datetime
from pyservices.data_descriptors.meta_model import MetaModel
from pyservices.data_descriptors.fields import StringField, IntegerField,\
    DateTimeField, ComposedField, ListField, ConditionalField, DictField

NoteMM = MetaModel('Note',
                   StringField('title'),
                   StringField('content'),
                   primary_key_name='title')
AccountMM = MetaModel('Account',
                      StringField('username'),
                      StringField('email'),
                      IntegerField('friends_number'),
                      IntegerField('id'),
                      primary_key_name='id')
UserMM = MetaModel('User',
                   StringField('username'),
                   AccountMM())
AddressMM = MetaModel(
            'Address',
            StringField('city'),
            StringField('postal_code'))
Address = AddressMM.get_class()
PersonMM = MetaModel(
            'Person',
            StringField('person_name'),
            DateTimeField('last_access'),
            ComposedField('credentials',
                          StringField('password'),
                          StringField('vocal_features')),
            AddressMM())
PersonMultipleAddressMM = MetaModel(
            'PersonMA', StringField('person_name'),
            DateTimeField('last_access'),
            ListField('addresses', data_type=AddressMM))

EmailMM = MetaModel('Email', StringField('address'),
                    DateTimeField('creation_date'))
UserEmailsMM = MetaModel('UserEmails', StringField('name'),
                         ListField('notes', data_type=StringField),
                         ListField('emails', data_type=EmailMM))

accessCF = ComposedField('access', StringField('secret'),
                         StringField('service'))
FirstConnectorMM = MetaModel('First_connector', StringField('app_id'),
                             StringField('token'), StringField('secret'))
SecondConnectorMM = MetaModel('Second_connector', StringField('token'),
                              accessCF)

ConnectorCF = ConditionalField('connector', {
    'first': FirstConnectorMM,
    'second': SecondConnectorMM}, evaluation_field_name='connector_type')

AccountConnectorsMM = MetaModel('AccountConnectors', StringField('email'),
                                ConnectorCF, StringField('connector_type'))
color_fields = DictField('colors')

PaletteMM = MetaModel('PaletteDictField', StringField('name'), color_fields)

Account = AccountMM.get_class()
User = UserMM.get_class()
Note = NoteMM.get_class()
PersonMultipleAddress = PersonMultipleAddressMM.get_class()
Person = PersonMM.get_class()
Credentials = PersonMM.fields[2].get_class()
Access = accessCF.get_class()
AccountConnectors = AccountConnectorsMM.get_class()
FirstConnector = FirstConnectorMM.get_class()
SecondConnector = SecondConnectorMM.get_class()
Palette = PaletteMM.get_class()
Email = EmailMM.get_class()
UserEmails = UserEmailsMM.get_class()

accounts = accounts = [
    Account('first_account', 'first@email.com', 2314, 1),
    Account('second_account', 'second@email.com', 5443, 2),
    Account('second_account', 'second223@email.com', 5443, 3),
    Account('third_account', 'third@email.com', 34125, 4)]
users = [User('first_user', accounts[0])]
notes = [Note('FirstTitle', 'Content1234')]

addresses = [Address('MyCity', '44444'), Address('MySecondCity', '53102')]
person_ma = PersonMultipleAddress('MyPersonMultipleAddress', datetime.now(), addresses)

first_conn_auth = FirstConnector('my_app_id', 'my_token', 'my_secret')

second_conn_auth = SecondConnector('token', Access('my_secret', 'my_service'))

first_type_account = AccountConnectors('my@email.com', first_conn_auth,
                                       connector_type='first')

second_type_account = AccountConnectors('my@email.com', second_conn_auth,
                                        connector_type='second')
obj_repr = {
    'colors': {
        'red': '#ff0000',
        'green': '#00ff00',
        'blue': '#0000ff'},
    'name': 'my_palette'}
