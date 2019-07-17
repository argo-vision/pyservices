import unittest
from pyservices.data_descriptors.fields import *
from pyservices.utilities.exceptions import ModelInitException, MetaTypeException
from test.meta_models import *


# TODO refactor
# TODO ListField of ListField not supported yet
class TestDataDescriptor(unittest.TestCase):

    def testField(self):
        self.assertRaises(TypeError, Field)
        self.assertRaises(ValueError, BooleanField, name='Title')

    def testDateTimeField(self):
        dt = datetime.now()
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
        field = IntegerField('my_field')
        self.assertRaises(ValueError, MetaModel, 'ModelName',
                          field, field)

    def testGeneratedClassBasicUsage(self):
        now = datetime.now()
        email = Email('my@email.com', now)
        self.assertEqual(email.address, 'my@email.com')
        self.assertEqual(email.creation_date, now)

    def testGeneratedClassOnInstanceArguments(self):
        self.assertRaises(ModelInitException, Email, 'Definitively', 'Too',
                          'Many', 'Args')
        self.assertRaises(ModelInitException, Note, title='title',
                          not_existent_method='Trows exception')
        self.assertRaises(ModelInitException, Note, 'title', title='title')

    def testGeneratedClassOnFieldConstraints(self):
        self.assertRaises(ModelInitException, Account, username=123)

    def testGeneratedClassIdempotence(self):
        self.assertIsInstance(Email('MyTitle'), EmailMM.get_class())
        self.assertEqual(EmailMM.get_class(), EmailMM.get_class())

    def testComposedField(self):
        access_class = accessCF.get_class()
        a = access_class('secret', 'service')
        self.assertEqual(a.secret, 'secret')

    def testListField(self):
        emails = [Email('test@test.com', datetime.now()),
                  Email('second@test.com', datetime.now())]
        user = UserEmails('UserName', ['Note1', 'Note2', 'Note3'],
                          emails)
        self.assertEqual(user.emails[0].address, emails[0].address)
        self.assertListEqual(user.notes, ['Note1', 'Note2', 'Note3'])
        self.assertRaises(ModelInitException, User, 'UserName',
                          ['Note1', 1, 'Note3'], emails)
        UserEmails('UserName', None, emails)

    def testNestedSequences(self):
        # TODO not working
        pass
        # email_mm = MetaModel('EmailTestNestedSeq', StringField('address'),
        #                      DateTimeField('creation_date'))
        # Email = email_mm.get_class()
        # emails = [Email('test@test.com', datetime.now()),
        #           Email('second@test.com', datetime.now())]
        # seq_seq_mm = MetaModel('SeqseqTestNestedSeq',
        #                        ListField(
        #                            'outer',
        #                            data_type=ListField(
        #                                'innter',
        #                                data_type=email_mm)))
        # SeqSeq = seq_seq_mm.get_class()
        # seq_seq = SeqSeq([emails, emails])

    def testIntegerField(self):
        number_mm = MetaModel('TwoDigitNumbTestIntegerField',
                              IntegerField('first_digit'),
                              IntegerField('second_field'))
        Numb = number_mm.get_class()
        n = Numb(1, 2)
        self.assertRaises(ModelInitException, Numb, 'not', 'numbers')

    def testConditionalField(self):
        self.assertEqual(first_type_account.connector.secret, 'my_secret')
        self.assertEqual(second_type_account.connector.access.service,
                         'my_service')

    def testDictField(self):
        p = Palette('my_palette', {
            'red': '#ff0000',
            'green': '#00ff00',
            'blue': '#0000ff'})

        self.assertEqual(p.colors['red'], '#ff0000')

    # TODO once I create the ComposedField inside the MetaModel I cannot access
    #  the class (and instantiate an obj)
    def testDeepMetaModel(self):
        self.assertRaises(ModelInitException,
                          Person,
                          'username',
                          datetime.now(),
                          'not a CredentialModel type')
        user_instance = Person('my_username', datetime.now(),
                               Credentials('my_pass', 'my_vocalFeats'))
        self.assertIsInstance(user_instance, Person)
        self.assertIsInstance(user_instance.credentials, Credentials)

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
        id_mm = MetaModel('IdTestPrimaryKey',
                          StringField('name'),
                          StringField('surname'),
                          DateTimeField('birth_date'),
                          IntegerField('favourite_number'))
        person_mm = MetaModel('PersonID', id_mm('id'), primary_key_name='id')
        id1_repr = {
            'name': 'MyName',
            'surname': 'MySurname',
            'birth_date': datetime(2019, 4, 11, 15, 37, 46, 314931),
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
                'birth_date': datetime(2019, 4, 11, 15, 37, 46, 314931)
            }]
        self.assertRaises(ValueError, person_mm.validate_id,
                          **illegal_ids[0])
        self.assertRaises(ModelInitException, person_mm.validate_id,
                          **illegal_ids[1])


if __name__ == '__main__':
    unittest.main()
