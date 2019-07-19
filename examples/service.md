# Service
##Interfaces
####RESTFUL
```python
        class AccountManager(pyservices.layer_supertypes.Service):
            base_path = 'account-manager'

            class User(pyservices.interfaces.RestResourceInterface):
                meta_model = user_meta_model

                @staticmethod
                def collection(self):
                    # access the data in some ways
                    users = some_ways()
                    return users 

            class Account(pyservices.interfaces.RestResourceInterface):
                meta_model = account_meta_model
                resource_path = 'accounts'                  # default behaviour
                codec = pyservices.entity_codecs.JSON       # default behaviour

                @staticmethod
                def collection():
                    accounts = some_ways()                  # access the data in some ways
                    return accounts 

                @staticmethod
                def detail(res_id):
                    account = some_ways()                   # access the data in some ways
                    return account

                @staticmethod
                def add(account):
                    some_ways(account, account)             # add a resource in some ways

                @staticmethod
                def update(res_id, account):
                    some_ways(res_id, account)              # update the resource in some ways

                @staticmethod
                def delete(res_id):
                    some_ways(res_id)                       # delete the resource in some ways
```