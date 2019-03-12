import abc


# TODO class method approach?
class RestfulResource(abc.ABC):
    """Restful interface of a single Resource.

    """
    interface_type_id = 'RESTFUL'
    meta_model = None
    resource_path = None
    codec = None

    @classmethod
    def collection(cls): pass

    @classmethod
    def detail(cls): pass

    @classmethod
    def add(cls): pass

    @classmethod
    def update(cls): pass

    @classmethod
    def delete(cls): pass
