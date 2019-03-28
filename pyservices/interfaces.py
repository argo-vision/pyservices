import abc


class InterfaceBase(abc.ABC):
    # TODO docs
    interface_type_id = None

    def __init__(self, service):
        self.service = service


class RestResource(InterfaceBase):
    """Restful interface of a single Resource.

    """
    interface_type_id = 'RESTFUL'  # TODO is it really necessary?
    meta_model = None
    resource_path = None
    codec = None

    def collect(self): pass

    def detail(self, res_id): pass

    def add(self, resource): pass

    def update(self, res_id, resource): pass

    def delete(self, res_id): pass


class MessageInterface(InterfaceBase):
    # TODO
    pass
