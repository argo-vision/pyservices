import abc 
from datetime import datetime
from typing import NewType, Callable, TypeVar, Sequence, Optional, Union
from pyservices.exceptions import ModelInitException


class Field(abc.ABC):
    """Abstract class which represents a field in a MetaModel.

    Class attributes:
        T(type): The generic param used in the field_type.

    Attributes:
        name (str): The name of the field. The first letter of the name must be
            in lowercase. The capitalized name may indicate the field_type
            of the field
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


# TODO is it ok to identify uniquely the MetaModel with the name? #S1
class MetaModel:
    """Abstract class which represent the description of the model.

    Class attributes:
        FieldType(type): The type of Field.
        modelClasses(dict): A static


    Attributes:
        name(str): The name of the class which will be generated. It also define
            will be a key on the modelClasses
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
                If the name is already taken by another MetaModel # TODO S1
        """

        if str.islower(name[0]):
            raise ValueError('The case of the name must be uppercase')

        if MetaModel.modelClasses.get(name):
            raise ModelInitException('"{}" is already used by another MetaModel'
                                     .format(name))
        if not isinstance(name, str):
            raise TypeError(
                'The first argument must be the name of the composed field.')
        for arg in args:
            if not isinstance(arg, Field):
                raise TypeError(
                    'A {} type is not a valid type. A {} is expected.'
                    .format(type(arg), Field))
        title_set = {field.name for field in args}
        if len(title_set) < len(args):
            raise ValueError('Fields must have unique name')

        self.name = name
        self.fields = args

        # TODO Based on #S1 assumption
        MetaModel.modelClasses[self.name] = self._generate_class()

    def __call__(self, name: str = None):
        """Returns a ComposedField created from the field of the MetaModel

        """
        if not name:
            name = str.lower(self.name[0]) + self.name[1:]
        return ComposedField(name, *self.fields)

    def get_class(self):
        """Returns the class of the model described by the MetaModel instance.

        """
        return MetaModel.modelClasses.get(self.name)

    def _generate_class(self):
        """Generate the class based on the fields of the meta model.

        Raises:
            ModelInitException:
                - Too many args.
                - Unknown key in kwargs.
                - Inconsistency between args and kwargs.
                - Default type error.
                - No value, no optional.
                - Bad value type.
        """
        def new(cls, *args, **kwargs):
            if max(len(args), len(kwargs)) > len(self.fields):
                raise ModelInitException('There are too many arguments.')
            if not set(kwargs.keys()).issubset(
                    {field.name for field in self.fields}
            ):
                raise ModelInitException('Unknown key in kwargs.')
            field_values = {
                field.name: arg for arg, field in zip(args, self.fields)
            }
            if not set(kwargs.keys()).isdisjoint(set(field_values.keys())):
                raise ModelInitException(
                    'Inconsistencies between args and kwargs.'
                )
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
                                'The default value has a bad type {}. '
                                'Expected {}'
                                .format(type(value), field_values.field_type)
                            )
                        field_values[field.name] = value
                    elif not field.optional:
                        raise ModelInitException(
                            'The field named "{}" is not optional.'
                            .format(field.name)
                        )
                elif not isinstance(value, field.field_type):
                    raise ModelInitException(
                        '{}({}) is not an instance of {}.'
                        .format(value, type(value), field.field_type)
                    )

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
                 default: Union[datetime, Callable[..., datetime], None] = None,
                 optional: Optional[bool] = False) -> None:
        super().__init__(name, datetime, default, optional)


# TODO #S2 hierarchy
class ComposedField(Field):
    """A group of fields.

    This class inherits from Field.
    If a ComposedField is initialized through a MetaModel __call__ method,
        the field_type is already cached on MetaModel.modelClasses.
    The field_type is obtained from the MetaModel

    """

    def __init__(self,
                 name: str,
                 *args: Sequence[MetaModel.FieldType],
                 optional: Optional[bool] = False) -> None:
        try:
            field_type = MetaModel(name.capitalize(), *args).get_class()
        except ModelInitException:
            field_type = MetaModel.modelClasses.get(name.capitalize())
        super().__init__(name, field_type, None, optional)
