import unittest
from pyservices.data_descriptors.fields import *


# TODO refactor
# TODO ListField of ListField not supported
class TestDataDescriptor(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime.now()
        self.title_field = StringField(name='title')
        self.content_field = StringField(name='content')
        self.date_time_field = DateTimeField(name='datetime', default=self.now)
        MetaModel.modelClasses = dict()
        self.note_mm = MetaModel(
            'Note',
            self.title_field,
            self.content_field,
            self.date_time_field)
        self.Note = self.note_mm.get_class()

    def testField(self):
        self.assertRaises(TypeError, Field)
        self.assertRaises(ValueError, BooleanField, name='Title')

    def testDateTimeField(self):
        dt = datetime.datetime.now()
        dtf = DateTimeField('date', dt)
        dtc = MetaModel('TestDateTimeModel', dtf).get_class()
        inst = dtc(dt)
        self.assertEqual(dt, inst.date)
        inst = dtc(dt.timestamp())
        self.assertEqual(dt, inst.date)
        inst = dtc(dt.isoformat())
        self.assertEqual(dt, inst.date)

    def testMetaModelWithNotFieldArgs(self):
        self.assertRaises(MetaTypeException, MetaModel,
                          'MetaModel Name', 'Not a field')

    def testRepetitiveFieldName(self):
        self.assertRaises(ValueError, MetaModel, 'ModelName',
                          self.title_field, self.title_field)

    def testGeneratedClassBasicUsage(self):
        note = self.Note(title='Lorem Ipsum')
        self.assertEqual(note.title, 'Lorem Ipsum')
        self.assertEqual(note.datetime, self.now)

    def testGeneratedClassOnInstanceArguments(self):
        self.assertRaises(ModelInitException, self.Note, 'Definitively', 'Too',
                          'Many', 'Args')
        self.assertRaises(ModelInitException, self.Note, title='title',
                          not_existent_method='Trows exception')
        self.assertRaises(ModelInitException, self.Note, 'title', title='title')

    def testGeneratedClassOnFieldConstraints(self):
        self.assertRaises(ModelInitException, self.Note, title=1)

    def testGeneratedClassIdempotence(self):
        self.assertIsInstance(self.Note('MyTitle'),
                              self.note_mm.get_class())
        self.assertEqual(self.note_mm.get_class(),
                         self.note_mm.get_class())

    def testComposedField(self):
        post_mm = MetaModel('Post', self.title_field, self.content_field)
        ComposedField('post', self.title_field, self.content_field)
        ComposedField('post', self.title_field, self.content_field)

    def testListField(self):
        email_mm = MetaModel('Email', StringField('address'),
                             DateTimeField('creation_date'))
        user_mm = MetaModel('User', StringField('name'),
                            ListField('notes', data_type=StringField),
                            ListField('emails', data_type=email_mm))

        Email = email_mm.get_class()
        emails = [Email('test@test.com', datetime.datetime.now()),
                  Email('second@test.com', datetime.datetime.now())]
        user_cls = user_mm.get_class()
        user = user_cls('UserName', ['Note1', 'Note2', 'Note3'],
                        emails)
        self.assertEqual(user.emails[0].address, emails[0].address)
        self.assertListEqual(user.notes, ['Note1', 'Note2', 'Note3'])
        self.assertRaises(ModelInitException, user_cls, 'UserName',
                          ['Note1', 1, 'Note3'], emails)
        user_cls('UserName', None, emails)

    def testNestedSequences(self):
        # TODO not working
        pass
        # email_mm = MetaModel('Email', StringField('address'),
        #                      DateTimeField('creation_date'))
        # Email = email_mm.get_class()
        # emails = [Email('test@test.com', datetime.datetime.now()),
        #           Email('second@test.com', datetime.datetime.now())]
        # seq_seq_mm = MetaModel('Seqseq',
        #                        ListField(
        #                            'outer',
        #                            data_type=ListField(
        #                                'innter',
        #                                data_type=email_mm)))
        # SeqSeq = seq_seq_mm.get_class()
        # seq_seq = SeqSeq([emails, emails])

    def testIntegerField(self):
        number_mm = MetaModel('TwoDigitNumb',
                              IntegerField('first_digit'),
                              IntegerField('second_field'))
        Numb = number_mm.get_class()
        n = Numb(1, 2)
        self.assertRaises(ModelInitException, Numb, 'not', 'numbers')

    def testConditionalField(self):
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
        self.assertEqual(first_type_account.connector.secret, 'my_secret')
        self.assertEqual(second_type_account.connector.access.service,
                         'my_service')

    def testDictField(self):
        color_fields = DictField('colors')
        palette_meta_model = MetaModel('Palette', StringField('name'),
                                       color_fields)
        Palette = palette_meta_model.get_class()

        p = Palette('my_palette', {
            'red': '#ff0000',
            'green': '#00ff00',
            'blue': '#0000ff'})

        self.assertEqual(p.colors['red'], '#ff0000')

    # TODO once I create the ComposedField inside the MetaModel I cannot access
    #  the class (and instantiate an obj)
    def testDeepMetaModel(self):
        credential_meta_model = MetaModel(
            'Credentials',
            StringField('password'),
            StringField('vocalFeatures'))
        user_meta_model = MetaModel(
            'User',
            StringField('username'),
            StringField('email'),
            credential_meta_model(),
            ComposedField('address',
                          StringField('city'),
                          StringField('postalCode')))

        self.assertRaises(ModelInitException,
                          user_meta_model.get_class(),
                          'username',
                          'email',
                          'not a CredentialModel type')
        user_class = user_meta_model.get_class()
        credential_class = credential_meta_model.get_class()
        user_instance = user_class('my_username',
                                   'my_email',
                                   credential_class('my_pass',
                                                    'my_vocalFeats'))
        self.assertIsInstance(user_instance, user_class)
        self.assertIsInstance(user_instance.credentials, credential_class)

    def testMetaModelFields(self):
        model_a = MetaModel('A')
        self.assertEqual(0, len(model_a.fields))

        model_b0 = MetaModel('B0', StringField('a'))
        self.assertEqual(1, len(model_b0.fields))

        model_b1 = MetaModel('B1', StringField('a'), primary_key_name='a')
        self.assertEqual(1, len(model_b1.fields))

        model_c0 = MetaModel('C0', StringField('id'))
        self.assertEqual(1, len(model_c0.fields))

        model_c1 = MetaModel('C1', StringField('id'), primary_key_name='id')
        self.assertEqual(1, len(model_c1.fields))

        model_d0 = MetaModel('D0', StringField('id0'), StringField('id1'),
                             primary_key_name='id0')
        self.assertEqual(2, len(model_d0.fields))

        model_e0 = MetaModel('E0', ComposedField('a', StringField('a'),
                                                 StringField('b')))
        self.assertEqual(1, len(model_e0.fields))

    def testSimpleFieldInitValueStrict(self):
        int_field = IntegerField('integer_f')
        str_field = StringField('string_f')
        float_field = FloatField('float_f')
        v1 = int_field.init_value('123', strict=False)
        v2 = str_field.init_value(123, strict=False)
        v3 = float_field.init_value('123', strict=False)
        self.assertEqual(v1, 123)
        self.assertEqual(v2, '123')
        self.assertEqual(v3, 123.0)

    def testMetaModelEmptyInit(self):
        mm = MetaModel('MyEmptyNote', StringField('title'),
                       StringField('content'), IntegerField('likes'),
                       ComposedField('stuff', StringField('innerStuff')))
        empty_note = mm.get_class()()
        for field in mm.fields:
            self.assertIsNone(getattr(empty_note, field.name))

    def testPrimaryKeyValidation(self):
        id_mm = MetaModel('Id',
                          StringField('name'),
                          StringField('surname'),
                          DateTimeField('birth_date'),
                          IntegerField('favourite_number'))
        person_mm = MetaModel('Person', id_mm('id'), primary_key_name='id')
        id1_repr = {
            'name': 'MyName',
            'surname': 'MySurname',
            'birth_date': datetime.datetime(2019, 4, 11, 15, 37, 46, 314931),
            'favourite_number': '42'}
        id_validated = person_mm.validate_id(**id1_repr)

        id1_repr['favourite_number'] = 42
        for k, v in id1_repr.items():
            self.assertEqual(getattr(id_validated, k), v)

        illegal_ids = [
            {
                'name': 'MyName',
                'surname': 'MySurname',
                'birth_date': 'NOT A VALID DATE',
                'favourite_number': '42'},
            {
                'name': 'MyName',
                'surname': 'MySurname',
                'birth_date': datetime.datetime(2019, 4, 11, 15, 37, 46, 314931)
            }]
        self.assertRaises(ValueError, person_mm.validate_id,
                          **illegal_ids[0])
        self.assertRaises(ModelInitException, person_mm.validate_id,
                          **illegal_ids[1])


if __name__ == '__main__':
    unittest.main()
