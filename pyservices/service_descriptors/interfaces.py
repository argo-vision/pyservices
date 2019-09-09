import abc
import inspect
import logging
from enum import Enum
from functools import wraps
from typing import NamedTuple

from pyservices import JSON
from pyservices.data_descriptors.entity_codecs import Codec
from pyservices.data_descriptors.fields import ComposedField
from pyservices.utils.exceptions import InterfaceDefinitionException
from pyservices.utils.gcloud import check_if_gcloud

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

    def start(self):
        pass

    def stop(self):
        pass

    @staticmethod
    def _get_calls(it, typecheck):
        return {method[0]:
                    HTTP_op()(method[1]) for method
                in inspect.getmembers(it, lambda m: typecheck(m))
                if not (method[0].startswith('_') or method[0] == "start" or method[0] == "stop")}

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
            collect_exposition = {c.exposition for c in collects}
            if len(collect_exposition) > 1:
                raise InterfaceDefinitionException('Multiple expositions for '
                                                   'all the collects is not '
                                                   'supported.')
            setattr(collect, 'exposition', collect_exposition.pop())
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
                                                codec, codec,
                                                exposition=m.exposition)

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

    codec = JSON

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


def RPC(path=None, method="post"):
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
        return wrapped_rpc_call

    return my_decorator


class EventInterface(HTTPInterface):
    """RPC interface used to perform remote procedure calls.
    """
    queue_type = None
    queue_configuration = None
    codec = JSON

    def __init__(self, service):
        super().__init__(service)
        self.queue = None

    def start(self):
        from pyservices.utils.queues import get_queue
        if self.queue is None:
            self.queue = get_queue(self.queue_type, self.queue_configuration)

    def _get_instance_calls(self):
        """

        Returns:
            All public methods of rpc interface. Every method is tagged with RPC descriptor
         TODO Actual remote procedure calls (with self etc..) """
        return {n: event()(m) for n, m in super()._get_instance_calls().items()}

    def _get_http_operations(self):
        def create_descriptor(method):
            return InterfaceOperationDescriptor(
                interface=self,
                method=method,
                http_method=method.http_method,
                path=f'{self._get_endpoint()}/{method.path}',
                exposition=method.exposition)

        # TODO: exposition must be gcloud dependent

        return [create_descriptor(m) for m in self._get_instance_calls().values()]


def event(path=None, method="GET"):
    """
    Decorator event (idempotent)
     TODO: more security?
    """

    def my_decorator(func):
        if hasattr(func, 'path'):
            return func
        relative_path = path or func.__name__.replace('_', '-')
        http_method = method.lower()

        @wraps(func)
        def dispatcher(self, *args, **params):
            func.path = relative_path
            func.http_method = http_method

            def enqueue_message(params):
                try:
                    task = self.queue.build_task(self.service, self, func, params)
                    return self.queue.add_task(task)
                except Exception as e:
                    logger.error("Cannot enqueue message: {}".format(e))
                    return "nack"

            def process_message(params):
                # TODO: Manage security and other "container" stuff (log, audit, ...).

                func(self, **params)

            def dispatch_message(params):
                op = process_message if self.queue.is_processing() else enqueue_message
                return op(params)

            # Dispatching:
            return dispatch_message(params)

        # Some data to add to the operation-descriptor:
        if check_if_gcloud():
            dispatcher.exposition = HTTPExposition.MANDATORY
        elif hasattr(func, 'exposition'):
            dispatcher.exposition = func.exposition
        else:
            dispatcher.exposition = HTTPExposition.ON_DEPENDENCY

        dispatcher.http_method = http_method
        dispatcher.path = relative_path

        # The decorated call is the dispatcher:
        return dispatcher

    return my_decorator


def HTTP_op(exposition: HTTPExposition = HTTPExposition.ON_DEPENDENCY):
    """
    Decorator for every HTTP operation
    Args:
        exposition (HTTPExposition): The exposition of the call
    """

    def my_decorator(func):
        if hasattr(func, 'exposition'):
            return func

        @wraps(func)
        def http_operation(*args, **kwargs):
            return func(*args, **kwargs)

        http_operation.exposition = exposition
        return http_operation

    return my_decorator
