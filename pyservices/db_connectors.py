from abc import ABC, abstractmethod


# TODO pattern
class DBConnector(ABC):

    @abstractmethod
    def __init__(self):
        pass


class MongoConnector(DBConnector):
    def __init__(self, config):
        # TODO
        super().__init__()
