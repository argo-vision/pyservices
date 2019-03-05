from abc import ABC


class Model(ABC):
    pass


# TODO docstrings
class Service:

    def __init__(self, config: dict = None):
        self.config = config
