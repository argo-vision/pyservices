import abc
import datetime
import uuid
from typing import Callable, TypeVar, Union, Mapping

from pyservices.utilities.exceptions import ModelInitException, MetaTypeException
from pyservices.data_descriptors.meta_model import MetaModel


class Field(abc.ABC):
    """ Abstract class which represents a field in a MetaModel.

    Class attributes:
        T (typing.TypeVar): The generic param used in the field_type.
    """
    _T = TypeVar('_T')

    @abc.abstractmethod
    def __init__(self,
                 name: str,
                 field_type: _T,
                 default: Union[_T, Callable[..., _T], None] = None) -> None:
        """ Initialize the field.

        Attributes:
            name (str): The name of the field. The first letter of the name must
                be in lowercase. The capitalized name may indicate the
                field_type of the field.
            field_type (_T): The type of the related field.
            default (Union[_T, Callable[...,_T], None]): Could be either a
                field_type object or a callable object returning a field_type
                object. Defaults to None.

        Raises:
            ValueError:
                If the first letter of the provided name is uppercase.
        """
        if str.isupper(name[0]):
            raise ValueError('The case of the name must be lowercase.')
        self.name = name
        self.field_type = field_type
        self.default = default

    def __repr__(self) -> str:
        return '<Field {}:{}[{};{}]>'.format(
            self.name,
            self.__class__.__name__,
            self.field_type.__name__,
            self.default)

    def init_value(self, value, strict: bool = True):
        """ Return the value of a correct type.

        If the field_type is not a builtin, it may be necessary to perform
            some operations to value.

        Attributes:
            value: The value used to initialize the model.
            strict (bool): Flag used to perform a strict initialization.

        Returns:
            _T: The value of a correct type.

        Raises:
            ModelInitException:
                If the type value does not match with field_type.
        """
        # noinspection PyTypeHints
        if not isinstance(value, self.field_type):
            raise ModelInitException(
                f'{value}({type(value)}) is not an instance of '
                f'{self.field_type}.')
        return value


class SimpleField(Field):
    """A SimpleField is Field with a static build in field_type.

    Class attributes:
        static_field_type (type): The static type of the Field.

    """
    static_field_type = None

    def __init__(self,
                 name: str,
                 default: Union[static_field_type,
                                Callable[..., static_field_type], None] = None
                 ) -> None:
        super().__init__(name, self.__class__.static_field_type,
                         default)

    def init_value(self, value, strict: bool = True):
        """ Initialize a SimpleField.

        Attributes:
            value: The value used to initialize the data.
            strict (bool): Used tu perform a strict initialization.
                If False, some type conversions based on the static_field_type
                    are tried before initializing the field. (E.g. an Integer
                    field could be initialized with a '1' string value since it
                    could be casted to int.

        """
        if not strict:
            try:
                value = self.static_field_type(value)
            except TypeError:
                pass
        return super().init_value(value)


class StringField(SimpleField):
    """ A string field.
    """
    static_field_type = str


class BooleanField(SimpleField):
    """ A boolean field.
    """
    static_field_type = bool


class IntegerField(SimpleField):
    """ An integer field.
    """
    static_field_type = int


class FloatField(SimpleField):
    """ An integer field.
    """
    static_field_type = float


class DateTimeField(SimpleField):
    """ A datetime field.
    """
    static_field_type = datetime.datetime

    # TODO strict could be used as false to perform the following conversions on
    #  the _init_ of an extension of datetime.datetime
    def init_value(self, value, strict: bool = True):
        """ Initialize the datetime value.

        It initialize the datetime in different ways according to the type of
            value.
        """
        if isinstance(value, str):
            value = datetime.datetime.fromisoformat(value)
        elif isinstance(value, float):
            value = datetime.datetime.fromtimestamp(value)
        return super().init_value(value, strict)


class ComposedField(Field):
    """ A group of fields.

    If a ComposedField is initialized through a MetaModel __call__ method,
        the field_type is already cached on MetaModel.modelClasses.
    The field_type is obtained from the MetaModel.
    """

    def __init__(self,
                 name: str,
                 *args: Field,
                 meta_model: MetaModel = None) -> None:
        """ Initialize the ComposedField.

        Attributes:
            *args (Field); The fields which compose the
                ComposedField
            meta_model (type): The related MetaModel. If passed, the composed
                field is generated from an existing MetaModel. If not, a
                MetaModel is created from the ComposedField.
        """

        if meta_model:
            self.meta_model = meta_model
        else:
            self.meta_model = MetaModel(
                name.capitalize() + '_' + str(uuid.uuid4()), *args)
        super().__init__(name, self.meta_model.get_class(), None)

    def get_class(self):
        """ Return the class of the MetaModel.
        """
        return self.meta_model.get_class()

    def init_value(self, value, strict: bool = True):
        """ Initialize the ComposedField.

        Args:
            value: If the type is dict, the map represent the values used to
                initialize the meta model related to the ComposedField.
            strict (bool): Flag used to perform a strict initialization.

        Returns:
            An instance of the class of the meta model related to the composed
            field.
        """
        if isinstance(value, dict):
            for field in self.meta_model.fields:
                v = value.get(field.name, None)
                if v is None:
                    raise ModelInitException(f'The id is not valid. '
                                             f'"{field.name}"" is missing.')
                value[field.name] = field.init_value(v, strict=strict)
            value = self.meta_model.get_class()(**value)
        return super().init_value(value)


class ListField(Field):
    """ A list field.
    """

    def __init__(self,
                 name: str,
                 data_type: Union[SimpleField.__class__, MetaModel],
                 default: Union[list, Callable[..., list], None] = None
                 ) -> None:
        """ Initialize the ListField
        Attributes:
            data_type (Union[SimpleField.__class__, MetaModel]): An object used
                to discover the type of the data represented by this ListField.
        """
        if isinstance(data_type, MetaModel) \
                or issubclass(data_type, SimpleField):
            self.data_type = data_type
        else:
            raise MetaTypeException(f'The data_type must be either a '
                                    f'SimpleField or a MetaModel instance, not '
                                    f'a {type(data_type)}.')
        super().__init__(name, list, default)

    def init_value(self, value, strict: bool = True):
        """ Return the value of a correct type.

        Checks the type of the elements of the list.
        """
        value = super().init_value(value)
        if isinstance(self.data_type, MetaModel):
            t = self.data_type.get_class()
        elif issubclass(self.data_type, SimpleField):
            t = self.data_type.static_field_type
        else:
            raise MetaTypeException(f'The data_type must be either a '
                                    f'SimpleField or a MetaModel instance, not '
                                    f'a {type(self.data_type)}.')
        for el in value:
            # noinspection PyTypeHints
            if not isinstance(el, t):
                raise ModelInitException(f'The type of the {el} is not {t}')
        return value


class DictField(SimpleField):
    """ A field representing a dict.

    """
    static_field_type = dict


class ConditionalField(Field):
    """ A field with different MetaModels associated.

    """

    def __init__(self,
                 name: str,
                 meta_models: Mapping[str, MetaModel],
                 evaluation_field_name: str) -> None:
        """ Initialize the ConditionalField.

        The field_type is set to None and it will be dynamically evaluated when
            a new model is initialized.

        Attributes:
            meta_models (Mapping[str, MetaModel]): The dict containing the
                relations between field values and MetaModels.
            evaluation_field_name (str): The str which indicated the title of
                the field which will be used to select the right MetaModel.

        """
        self.meta_models = meta_models
        self.evaluation_field_name = evaluation_field_name
        super().__init__(name, None, None)

    def init_value(self, value, strict: bool = True):
        """I have to type check the value at when the new model is being
            created.

        Attributes:
            value (tuple): the first element must contain the value,
                the second element must contain the MetaModel identified(str)

        """
        conditional_meta_model = self.meta_models.get(value[1])
        if not conditional_meta_model:
            raise ModelInitException(f'There are no matching MetaModels '
                                     f'identified by {value[1]}.')
        return conditional_meta_model().init_value(value[0])
