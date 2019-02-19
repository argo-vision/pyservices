import unittest
from datetime import datetime
from pyservices.data_descriptor import MetaModel, StringField, \
    DateTimeField, Field, BooleanField, ComposedField
from pyservices.exceptions import ModelInitException


class TestDataDescriptor(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now()
        self.title_field = StringField(name='title')
        self.content_field = StringField(name='content', optional=True)
        self.date_time_field = DateTimeField(name='datetime', default=self.now)
        self.note_desc = MetaModel(
            'Note',
            self.title_field,
            self.content_field,
            self.date_time_field
        )
        self.Note = self.note_desc.generate_class()

    def testField(self):
        self.assertRaises(TypeError, Field)
        self.assertRaises(ValueError, BooleanField, name='title', optional=True, default=True)

    def testMetaModelField(self):
        self.assertRaises(ValueError, MetaModel, 'MetaModel Name', self.title_field, self.title_field)
        self.assertRaises(TypeError, MetaModel, 'MetaModel Name', 'Not a field')
        self.assertRaises(ValueError, MetaModel, 'Duplicated fields', self.title_field, self.title_field)

    def testRepetitiveFieldName(self):
        self.assertRaises(ValueError, MetaModel, 'ModelName', self.title_field, self.title_field)

    def testGeneratedClassBasicUsage(self):
        note = self.Note(title='Lorem Ipsum')
        self.assertEqual(note.title, 'Lorem Ipsum')
        self.assertEqual(note.datetime, self.now)

    def testGeneratedClassOnInstanceArguments(self):
        self.assertRaises(ModelInitException, self.Note, 'Definitively', 'Too', 'Many', 'Args')
        self.assertRaises(ModelInitException, self.Note, title='title', not_existent_method='Trows exception')
        self.assertRaises(ModelInitException, self.Note, 'title', title='title')

    def testGeneratedClassOnFieldConstraints(self):
        self.assertRaises(ModelInitException, self.Note)
        self.assertRaises(ModelInitException, self.Note, title=1)

# CredentialsModel = MetaModel(
#     StringField("password"),
#     StringField("vocalFeatures")
# )
    def testGeneratedClassIdempotence(self):
        # self.assertIsInstance(self.Note('MyTitle'), self.note_desc.generate_class())
        self.assertEqual(self.note_desc.generate_class(), self.note_desc.generate_class())

    def testComposedField(self):
        # TODO
        pass

    def testDeepMetaModel(self):
        CedentialModel = MetaModel(
            'Credentials',
            StringField('password'),
            StringField('vocalFeatures')
        )
        UserModel = MetaModel(
            'User',
            StringField('username'),
            StringField('email'),
            CedentialModel('Credentials')
        )
        self.assertRaises(ModelInitException,
                          UserModel.generate_class(),
                          'username',
                          'email',
                          'not a CredentialModel type')
        try:
            user_instance = UserModel.generate_class()('my_username',
                                                   'my_email',
                                                   CedentialModel.generate_class()('my_pass', 'my_vocalfeats'))
        except ModelInitException as e:
            self.fail(e)
        self.assertIsInstance(user_instance, UserModel.generate_class())



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
# Credentials = CredentialsModel.generate_class()
# User = UserModel.generate_class()