import unittest
from datetime import datetime
from pyservices.data_descriptors import MetaModel, StringField, DateTimeField, \
    Field, BooleanField, ComposedField
from pyservices.exceptions import ModelInitException


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

    def testMetaModelField(self):
        self.assertRaises(ValueError, MetaModel, 'metaModel Name',
                          self.title_field, self.title_field)
        self.assertRaises(ValueError, MetaModel, 'MetaModel Name',
                          self.title_field, self.title_field)
        self.assertRaises(TypeError, MetaModel, 'MetaModel Name', 'Not a field')
        self.assertRaises(ValueError, MetaModel, 'Duplicated fields',
                          self.title_field, self.title_field)

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

# CredentialsModel = MetaModel(
#     StringField("password"),
#     StringField("vocalFeatures")
# )
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



# UserModel = MetaModel(
#     StringField("nick"),
#     # ...
#     CredentialsModel("credentials")
#     # CompositeField("credentials",
#     #               StringField("password"),
#     #               StringField("vocalFeatures")
#     #       )
# )
#
# {
#     "nick": "Pippo",
#     # ...
#     "credentials": {
#         "pasword": "aaa",
#         "vocalFeatures": "bbb"
#     }
# }
#
# Credentials = CredentialsModel.get_class()
# User = UserModel.get_class()