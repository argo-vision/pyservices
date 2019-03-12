# Entity codecs
A Codec is an object used to encode and decode data. The Codec class is abstract and need to be subclassed.
###JSON
```python
user_meta_model = MetaModel('User', 
                    name_field, date_field,    # "Simple" fields
                    accounts_field,             # SequenceField
                    credentials_meta_model())   # ComposedField generated from a meta model         

user = User('my_name', datetime.datetime.today(), accounts=my_accounts, credentials=cred1)
```
### Encode
```python
str_repr = JSON.encode(user)
```

### Decode
```python
JSON.decode(str_repr, user_meta_model)
```