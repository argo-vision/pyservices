# Data descriptors
The data desriptors are necessary when we have a "plain" representation of a model and we need to re-construct the 
object instance.
### Fields
Abstract class which represents a field in a MetaModel.
```python
name_field = StringField('name')
name_field = StringField(name='name')
name_field = StringField('name', optional=True)


date_field = DateTimeField('created_at', default=datetime.datetime.now())  # datetime.datetime type
date_field = DateTimeField('created_at', default=datetime.datetime.now)    # callable returning datetime.datetime


account_field = ComposedField('account',
                    StringField('email'),
                    StringField('password'),
                    date_field)

accounts_field = SequenceField('accounts',
                    data_type=account_field,
                    optional=True)
```

## MetaModel
The description of a model is used when we have a "plain" representation of a model and we need to re-construct the 
object instance.
#### Definition
MetaModel initialization
A class which represents the description of the model.
```python

credentials_meta_model = MetaModel('Credentials', StringField('password'), 
                            StringField('vocalFeatures'))

user_meta_model = MetaModel('User', 
                    name_field, date_field,    # "Simple" fields
                    accounts_field,             # SequenceField
                    credentials_meta_model())   # ComposedField generated from a meta model         
```
#### Usage
```python
Credential = credentials_meta_model.get_class()
User = user_meta_model.get_class()
Account = account_field.meta_model.get_class()

cred1 = Credential('my_pass', 'my_vocals')
cred2 = Credential(password='my_pass', vocalFeatures='my_vocals')
cred3 = Credential('my_pass', vocalFeatures='my_vocals')

my_accounts = [Account('my_first_email', 'my_first_pass'), Account('my_second_email', 'my_second_pass')]

user1 = User('my_name', datetime.datetime.today(), accounts=my_accounts, credentials=cred1)
user2 = User('my_name', credentials=cred1)  # A default behaviour is defined for date_field
                                            # accounts_field is optional
```