import abc
from functools import wraps
import inspect

from pyservices import JSON


class InterfaceBase(abc.ABC):
    """Base class of interfaces. InterfaceBase subclasses describe interfaces.
    They are initialization and implementation independent.

    The methods of the class can be overloaded in a service implementation.

    Interface classes provide a descriptive information for the interface.
    Interface instances contains the reference to the services to which a given
        interface is linked
    """
    if_path = None

    def __init__(self, service):
        self.service = service

    def _get_calls(self):
        return {method[0]: method[1] for method in inspect.getmembers(
            self, lambda m: inspect.ismethod(m))
                if not method[0].startswith('_')}

    @classmethod
    def _get_call_descriptors(cls):
        return {method[0]: method[1] for method in inspect.getmembers(
            cls, lambda m: inspect.isfunction(m))
                if not method[0].startswith('_')}


class HTTPInterface(InterfaceBase):
    """Abstract HTTP interface.

    """

    @classmethod
    def _get_endpoint_name(cls):
        return cls.if_path


class RestResourceInterface(HTTPInterface):
    """Restful interface of a single REST resource.

    """
    meta_model = None
    codec = JSON

    def collect(self):
        """ Define the procedure used to collect list of resources.

        Different "collect"s methods can be defined. Their name must match
        this pattern: r'collect*'. These methods can have different parameters
        lists. The first matching method will be called.

        Returns:
            (list): A list of object of the class related the MetaModel of the
                RestResource interface.
        """
        pass

    def detail(self, res_id):
        """ Define the procedure used to get a single resource record/document.

        Args:
            res_id: A validated_id of the MetaModel. If the primary_key_field of
                the MetaModel is a ComposedField, res_id will be an instance of
                the ComposedField's related class. If the primary_key_field is a
                SimpleField, rees_id will be a native datatype, its type will be
                coherent with the static_field_type of the primary_key_field.

        Returns:
            An object of the class related the MetaModel of the RestResource
                interface.
        """
        pass

    def add(self, resource):
        """ Define the procedure used add the resource.

        Args:
            resource: The resource to add.


        Returns:
            (str): A str repr of the id of the resource.
                (E.g. StringField primary key will expect "str_id_value".
                ComposedField primary key will expect "firstFieldValue/sec/")
        """
        pass

    def update(self, res_id, resource):
        """ Define the procedure used to update a resource.

        Args:
            res_id: A validated_id of the MetaModel. If the primary_key_field of
                the MetaModel is a ComposedField, res_id will be an instance of
                the ComposedField's related class. If the primary_key_field is a
                SimpleField, rees_id will be a native datatype, its type will be
                coherent with the static_field_type of the primary_key_field.
            resource: The updated resource.

        """
        pass

    def delete(self, res_id):
        """ Define the procedure used to delete a resource.

        Args:
            res_id: A validated_id of the MetaModel. If the primary_key_field of
                the MetaModel is a ComposedField, res_id will be an instance of
                the ComposedField's related class. If the primary_key_field is a
                SimpleField, rees_id will be a native datatype, its type will be
                coherent with the static_field_type of the primary_key_field.
        """
        pass

    @classmethod
    def _get_endpoint_name(cls):
        return cls.if_path or f'{cls.meta_model.name.lower()}s'

    def _get_calls(self):
        methods = super()._get_calls()
        collect_methods_names = \
            filter(lambda k: k.startswith('collect'), methods)
        methods['collect'] = sorted(
            [methods.get(n) for n in collect_methods_names],
            key=lambda m: inspect.getsourcelines(m)[1])
        return methods


class RPCInterface(HTTPInterface):
    """RPC interface used to perform remote procedure calls.
    """

    def _get_calls(self):
        """ TODO Actual remote procedure calls (with self etc..) """
        return {n: RPC()(m) for n, m in super()._get_calls().items()}

    @classmethod
    def _get_call_descriptors(cls):
        """ TODO Actual remote procedure calls (with self etc..) """
        return {n: RPC()(c) for n, c in super()._get_call_descriptors().items()}


# TODO this decorator could be generalized for every HTTP call
def RPC(path=None, method="POST"):
    """
    Decorator remote procedure calls (idempotent)
     TODO
    """
    def RCP_call_decorator(func):
        if hasattr(func, 'path'):
            return func

        @wraps(func)
        def wrapped_rpc_call(*args, **kwargs):
            return func(*args, **kwargs)

        wrapped_rpc_call.method = method.lower()
        wrapped_rpc_call.path = path or func.__name__.replace('_', '-')
        return wrapped_rpc_call

    return RCP_call_decorator
