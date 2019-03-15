import unittest
from datetime import datetime

from pyservices.data_descriptors import MetaModel, StringField, DateTimeField, \
    Field, BooleanField, ComposedField, SequenceField, IntegerField, \
    ConditionalField, DictField
from pyservices.exceptions import ModelInitException, MetaTypeException


# TODO refactor
# TODO Sequence of SequenceField not working...
class TestDataDescriptor(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now()
        self.title_field = StringField(name='title')
        self.content_field = StringField(name='content', optional=True)
        self.date_time_field = DateTimeField(name='datetime', default=self.now)
        MetaModel.modelClasses = dict()
        self.note_desc = MetaModel(
            'Note',
            self.title_field,
            self.content_field,
            self.date_time_field)
        self.Note = self.note_desc.get_class()

    def testField(self):
        self.assertRaises(TypeError, Field)
        self.assertRaises(ValueError, BooleanField, name='title',
                          optional=True, default=True)
        self.assertRaises(ValueError, BooleanField, name='Title')

    def testDateTimeField(self):
        dt = datetime.now()
        try:
            dtf = DateTimeField('date', dt)
            dtc = MetaModel('TestDateTimeModel', dtf).get_class()
        except ModelInitException as e:
            self.fail(e)
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
        self.assertRaises(ModelInitException, self.Note)
        self.assertRaises(ModelInitException, self.Note, title=1)

    def testGeneratedClassIdempotence(self):
        self.assertIsInstance(self.Note('MyTitle'),
                              self.note_desc.get_class())
        self.assertEqual(self.note_desc.get_class(),
                         self.note_desc.get_class())

    def testComposedField(self):
        post_mm = MetaModel('Post', self.title_field, self.content_field)
        try:
            ComposedField('post', self.title_field, self.content_field)
            ComposedField('post', self.title_field, self.content_field)
        except ModelInitException as e:
            self.fail(e)

    def testSequenceField(self):
        email_mm = MetaModel('Email', StringField('address'),
                             DateTimeField('creation_date'))
        user_mm = MetaModel('User', StringField('name'),
                            SequenceField('notes', optional=False,
                                          data_type=StringField('note')),
                            SequenceField('emails', data_type=email_mm()))

        Email = email_mm.get_class()
        emails = [Email('test@test.com', datetime.now()),
                  Email('second@test.com', datetime.now())]
        user_cls = user_mm.get_class()
        try:
            user = user_cls('UserName', ['Note1', 'Note2', 'Note3'],
                            emails)
        except ModelInitException as e:
            self.fail(e)
        self.assertEqual(user.emails[0].address, emails[0].address)
        self.assertListEqual(user.notes, ['Note1', 'Note2', 'Note3'])
        self.assertRaises(ModelInitException, user_cls, 'UserName',
                          ['Note1', 1, 'Note3'], emails)
        self.assertRaises(ModelInitException, user_cls, 'UserName',
                          None, emails)

    def testNestedSequences(self):
        # TODO not working
        email_mm = MetaModel('Email', StringField('address'),
                             DateTimeField('creation_date'))
        Email = email_mm.get_class()
        emails = [Email('test@test.com', datetime.now()),
                  Email('second@test.com', datetime.now())]
        seq_seq_mm = MetaModel('Seqseq',
                               SequenceField(
                                   'outer',
                                   data_type=SequenceField(
                                       'innter',
                                       data_type=email_mm())))
        SeqSeq = seq_seq_mm.get_class()
        try:
            seq_seq = SeqSeq([emails, emails])
        except Exception as e:
            self.fail(e)

    def testIntegerField(self):
        number_mm = MetaModel('TwoDigitNumb',
                              IntegerField('first_digit'),
                              IntegerField('second_field'))
        Numb = number_mm.get_class()
        try:
            n = Numb(1, 2)
        except Exception as e:
            self.fail(e)
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

        try:
            p = Palette('my_palette', {
                'red': '#ff0000',
                'green': '#00ff00',
                'blue': '#0000ff'})
        except Exception as e:
            self.fail(e)
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
                          StringField('postalCode'),
                          optional=True))

        self.assertRaises(ModelInitException,
                          user_meta_model.get_class(),
                          'username',
                          'email',
                          'not a CredentialModel type')
        user_class = user_meta_model.get_class()
        credential_class = credential_meta_model.get_class()
        try:
            user_instance = user_class('my_username',
                                       'my_email',
                                       credential_class('my_pass',
                                                        'my_vocalFeats'))
        except ModelInitException as e:
            self.fail(e)
        self.assertIsInstance(user_instance, user_class)
        self.assertIsInstance(user_instance.credentials, credential_class)

