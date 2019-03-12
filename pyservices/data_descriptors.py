import abc
import datetime
import uuid

from typing import NewType, Callable, TypeVar, Sequence, Optional, Union

from pyservices.exceptions import ModelInitException


class Field(abc.ABC):
    """Abstract class which represents a field in a MetaModel.

    Class attributes:
        T(type): The generic param used in the field_type.

    Attributes:
        name (str): The name of the field. The first letter of the name must be
            in lowercase. The capitalized name may indicate the field_type
            of the field.
        field_type (T): The type of the related field.
        default(Union(T, Callable[...,T], None)): Could be either a field_type
            object or a callable object returning a field_type object.
            Defaults to None.
        optional(Optional(bool): A boolean indicating either the field will
            require a value(False) or don't(True). Defaults to None.
    """
    T = TypeVar('T')

    @abc.abstractmethod
    def __init__(self,
                 name: str,
                 field_type: T,
                 default: Union[T, Callable[..., T], None] = None,
                 optional: Optional[bool] = False) -> None:
        """ Initialize the field.

        Raises:
            ValueError:
                If a field has a default value if must be non optional.
                If the first letter of the provided name is uppercase.
        """
        if optional and default:
            raise ValueError('An optional field cannot have a default')
        if str.isupper(name[0]):
            raise ValueError('The case of the name must be lowercase')
        self.name = name
        self.field_type = field_type
        self.optional = optional
        self.default = default

    def init_value(self, value):
        """Return the value of a correct type.

        If the field_type is not a builtin, it may be necessary to perform
            some operations to value.

        Attributes:
            value: The value used to initialize the model.

        Returns:
            T: The value of a correct type.

        Raises:
            ModelInitException:
                If the type value does not match with field_type.
        """
        # TODO
        # noinspection PyTypeHints
        if not isinstance(value, self.field_type):
            raise ModelInitException(
                f'{value}({type(value)}) is not an instance of '
                f'{self.field_type}.')
        return value


class MetaModel:
    """ A class which represents the description of the model.

    Class attributes:
        FieldType(type): The type of Field.
        modelClasses(dict): A static dict used to store the generated classes.

    Attributes:
        name(str): The name of the class which will be generated. It also define
            will be a key on the modelClasses.
        fields(Sequence[FieldType]): The fields used to generate the class with
            _generate_class method.
    """
    FieldType = NewType('FieldType', Field)
    modelClasses = dict()

    def __init__(self,
                 name: str,
                 *args: Sequence[FieldType]):
        """Initialize the meta model.

        Raises:
            ValueError:
                If the first letter of the provided name is lowercase.
                If different fields contain the same name attribute.
            TypeError:
                If the first argument is not a string.
                If the args are not Field's subclass instances.
            ModelInitException:
                If the name is already taken by another MetaModel.
        """

        if MetaModel.modelClasses.get(name):
            raise ModelInitException(f'"{name}" is already used by another '
                                     f'MetaModel')
        if not isinstance(name, str):
            raise TypeError(
                'The first argument must be the name of the composed field.')

        if str.islower(name[0]):
            raise ValueError('The case of the name must be uppercase')

        for arg in args:
            if not isinstance(arg, Field):
                raise TypeError(
                    f'A {type(arg)} type is not a valid type. A {Field} is '
                    f'expected.')
        title_set = {field.name for field in args}
        if len(title_set) < len(args):
            raise ValueError('Fields must have unique name')

        self.name = name
        self.fields = args

        MetaModel.modelClasses[self.name] = self._generate_class()

    def __call__(self, name: str = None):
        """Returns a ComposedField created from the fields of the MetaModel.
        """
        if not name:
            name = str.lower(self.name[0]) + self.name[1:]
        return ComposedField(name, meta_model=self)

    def get_class(self):
        """Returns the class representing the model described by the MetaModel.

        Returns:
            The class stored in the modelClasses dict identified by name as key.
        """
        return MetaModel.modelClasses.get(self.name)

    def _generate_class(self):
        """Generate the class based on the fields of the meta model.
        """
        def new(cls, *args, **kwargs):
            """Create and return a new instance of the model.
            Raises:
                ModelInitException:
                    If too many args are passes.
                    If an unknown key is present in kwargs.
                    If there are some inconsistencies between args and kwargs.
                    If the default type if wrong.
                    If no value is passed for a non optional field.
            """
            if max(len(args), len(kwargs)) > len(self.fields):
                raise ModelInitException('There are too many arguments.')
            if not set(kwargs.keys()).issubset(
                    {field.name for field in self.fields}):
                raise ModelInitException('Unknown key in kwargs.')
            field_values = {
                field.name: arg for arg, field in zip(args, self.fields)}
            if not set(kwargs.keys()).isdisjoint(set(field_values.keys())):
                raise ModelInitException(
                    'Inconsistencies between args and kwargs.')
            field_values = {**field_values, **kwargs}

            for field in self.fields:
                value = field_values.get(field.name)
                if not value:
                    if field.default:
                        if callable(field.default):
                            value = field.default()
                        else:
                            value = field.default
                        if not isinstance(value, field.field_type):
                            raise ModelInitException(
                                f'The default value has a bad type '
                                f'{type(value)}.Expected '
                                f'{field_values.field_type}'
                            )
                        field_values[field.name] = value
                    elif not field.optional:
                        raise ModelInitException(
                            f'The field named "{field.name}" is not optional.')
                else:
                    field_values[field.name] = field.init_value(value)

            instance = super(cls, cls).__new__(cls)  # TODO

            # TODO move this in __init__?
            for k, v in field_values.items():
                setattr(instance, k, v)

            return instance

        return type(self.name, (object,), {
            '__new__': new
        })


class StringField(Field):
    """A string field.
    """

    def __init__(self,
                 name: str,
                 default: Union[str, Callable[..., str], None] = None,
                 optional: Optional[bool] = False) -> None:
        super().__init__(name, str, default, optional)


class BooleanField(Field):
    """A boolean field.
    """

    def __init__(self,
                 name: str,
                 default: Union[bool, Callable[..., bool], None] = None,
                 optional: Optional[bool] = False) -> None:
        super().__init__(name, bool, default, optional)


class DateTimeField(Field):
    """A datetime field.
    """

    def __init__(self,
                 name: str,
                 default: Union[datetime.datetime,
                                Callable[..., datetime.datetime], None] = None,
                 optional: Optional[bool] = False) -> None:
        super().__init__(name, datetime.datetime, default, optional)

    def init_value(self, value):
        """Initialize the datetime value.
        It initialize the datetime in different ways according to the type of
            value.
        """
        if isinstance(value, str):
            value = datetime.datetime.fromisoformat(value)
        elif isinstance(value, float):
            value = datetime.datetime.fromtimestamp(value)
        return super().init_value(value)


# TODO is the name really necessary?
class ComposedField(Field):
    """A group of fields.

    This class inherits from Field.
    If a ComposedField is initialized through a MetaModel __call__ method,
        the field_type is already cached on MetaModel.modelClasses.
    The field_type is obtained from the MetaModel.
    """

    def __init__(self,
                 name: str,
                 *args: Sequence[MetaModel.FieldType],
                 optional: Optional[bool] = False,
                 meta_model: type = None) -> None:
        if meta_model:
            self.meta_model = meta_model
        else:
            self.meta_model = MetaModel(
                name.capitalize() + '_' + str(uuid.uuid4()), *args)
        super().__init__(name, self.meta_model.get_class(), None, optional)

    def get_class(self):
        """Return the class of the MetaModel.
        """
        return self.meta_model.get_class()
