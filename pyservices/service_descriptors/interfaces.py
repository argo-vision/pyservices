import abc
import inspect
import logging
from enum import Enum
from functools import wraps
from typing import NamedTuple

from pyservices import JSON
from pyservices.data_descriptors.entity_codecs import Codec
from pyservices.data_descriptors.fields import ComposedField

logger = logging.getLogger(__package__)


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

    @staticmethod
    def _get_calls(it, typecheck):
        return {method[0]: method[1] for method in inspect.getmembers(
            it, lambda m: typecheck(m))
                if not method[0].startswith('_')}

    def _get_instance_calls(self):
        """Get name - function of an interface as dictionary

        Returns:
        """
        return InterfaceBase._get_calls(self, inspect.ismethod)

    @classmethod
    def _get_class_calls(cls):
        return InterfaceBase._get_calls(cls, inspect.isfunction)


class HTTPInterface(InterfaceBase):
    """Abstract HTTP interface.

    """
    @abc.abstractmethod
    def _get_http_operations(self):
        """
        Inspects type(self) and generates the list of operations that can be exposed by the framework-app.

        Returns:
            List of InterfaceOperationDescriptor objects.
        """
        pass



    @classmethod
    def _get_interface_path(cls):
        return cls.if_path

    def _get_endpoint(self):
        return f'/{self.service.service_base_path}/{self._get_interface_path()}'


class HTTPExposition(Enum):
    """
    Exposition choices for an operation.
    NOTE: Expose all operations in development (also the forbidden ones).
    """
    MANDATORY = 0
    FORBIDDEN = 1
    ON_DEPENDENCY = 2


class InterfaceOperationDescriptor(NamedTuple):
    """
    Descriptor of a single remote HTTP operation.
    """
    interface: HTTPInterface
    method: callable
    http_method: str = "POST"
    path: str = ""
    encoder: Codec = JSON
    decoder: Codec = JSON
    exposition: HTTPExposition = HTTPExposition.ON_DEPENDENCY


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
    def _get_interface_path(cls):
        return cls.if_path or f'{cls.meta_model.name.lower()}s'

    def _get_instance_calls(self):
        methods = super()._get_instance_calls()
        collect_methods_names = \
            filter(lambda k: k.startswith('collect'), methods)
        methods['collect'] = sorted(
            [methods.get(n) for n in collect_methods_names],
            key=lambda m: inspect.getsourcelines(m)[1])
        return methods

    def _get_http_operations(self):
        methods = self._get_instance_calls()
        collects = methods.get('collect')
        if collects:
            collect = RestResourceInterface._get_merged_collect(collects)
            methods['collect'] = collect

        id_path = RestResourceInterface._get_meta_model_id_placeholder_path(self.meta_model)
        info = [
            ('collect', 'get'),
            ('detail', 'get', id_path),
            ('update', 'post', id_path),
            ('add', 'put'),
            ('delete', 'delete', id_path),
        ]
        return [self._interface_operation_descriptor(methods, *i) for i in info]

    def _interface_operation_descriptor(self, methods, method_name,
                                        http_method, path=None):
        m = methods.get(method_name)
        base_path = self._get_endpoint()
        if path:
            base_path = f'{base_path}/{path}'

        codec = self.codec
        if m:
            return InterfaceOperationDescriptor(self, m, http_method, base_path,
                                                codec, codec)

    @staticmethod
    def _get_merged_collect(collects):
        def merged_collect(*args, **kwargs):
            actual = None
            for c in collects:
                try:
                    sg = inspect.signature(c)
                    sg.bind(**kwargs)
                    actual = c
                    break
                except TypeError:
                    continue
            if actual:
                return actual(**kwargs)
            else:
                raise TypeError
        return merged_collect

    @staticmethod
    def _get_meta_model_id_placeholder_path(meta_model):
        if isinstance(meta_model.primary_key_field, ComposedField):
            id_dimension = len(
                meta_model.primary_key_field.meta_model.fields)
        else:
            id_dimension = 1
        return '/'.join(['{{id_field_{}}}'.format(i) for i in range(id_dimension)])


class RPCInterface(HTTPInterface):
    """RPC interface used to perform remote procedure calls.
    """

    def _get_instance_calls(self):
        """

        Returns:
            All public methods of rpc interface. Every method is tagged with RPC descriptor
         TODO Actual remote procedure calls (with self etc..) """
        return {n: RPC()(m) for n, m in super()._get_instance_calls().items()}

    def _get_http_operations(self):
        methods = self._get_instance_calls().values()
        return [InterfaceOperationDescriptor(self, m, m.http_method,
                                             f'{self._get_endpoint()}/{m.path}',
                                             exposition=m.exposition)
                for m in methods]

    @classmethod
    def _get_class_calls(cls):
        """ TODO Actual remote procedure calls (with self etc..) """
        return {n: RPC()(c) for n, c in super()._get_class_calls().items()}


def RPC(path=None, method="post",
        exposition: HTTPExposition = HTTPExposition.ON_DEPENDENCY):
    """
    Decorator remote procedure calls (idempotent)
     TODO
    """

    def my_decorator(func):
        if hasattr(func, 'path'):
            return func

        @wraps(func)
        def wrapped_rpc_call(*args, **kwargs):
            return func(*args, **kwargs)

        wrapped_rpc_call.http_method = method.lower()
        wrapped_rpc_call.path = path or func.__name__.replace('_', '-')
        wrapped_rpc_call.exposition = exposition
        return wrapped_rpc_call

    return my_decorator
