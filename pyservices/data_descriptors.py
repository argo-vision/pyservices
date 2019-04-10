import abc
import copy
import datetime
import uuid
from typing import NewType, Callable, TypeVar, Sequence, Optional, Union, \
    Mapping

import pyservices as ps
from pyservices.exceptions import ModelInitException, MetaTypeException


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
            raise ValueError('The case of the name must be lowercase')
        self.name = name
        self.field_type = field_type
        self.default = default

    def __repr__(self):
        return '<Field {}:{}[{};{}]>'.format(
            self.name,
            self.__class__.__name__,
            self.field_type.__name__,
            self.default)

    def init_value(self, value):
        """ Return the value of a correct type.

        If the field_type is not a builtin, it may be necessary to perform
            some operations to value.

        Attributes:
            value: The value used to initialize the model.

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


class MetaModel:
    """ A class which represents the description of the model.

    Class attributes:
        modelClasses (dict): A static dict used to store the generated classes.
    """
    modelClasses = dict()

    def __init__(self,
                 name: str,
                 *args: Field,
                 primary_key_name: Optional[str] = None):
        """ Initialize the meta model.

        Attributes:
            name (str): The name of the class which will be generated. It also
                define will be a key on the modelClasses.
            fields (Field): The fields used to generate the class
                with _generate_class method.
            primary_key_name (Optional[str]): The name of the field which will
                be the used as primary key for the model.

        Raises:
            ValueError:
                If the first letter of the provided name is lowercase.
                If different fields contain the same name attribute.
            TypeError:
                If the first argument is not a string.
            ModelInitException:
                If the name is already taken by another MetaModel.
            MetaTypeException:
                If the args are not Field's subclass instances.

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
                raise MetaTypeException(
                    f'A {type(arg)} type is not a valid type. A {Field} is '
                    f'expected.')
            if arg.name.startswith('_'):
                raise MetaTypeException(
                    f'A field name cannot begin with an "_".')
        title_set = {field.name for field in args}
        if len(title_set) < len(args):
            raise ValueError('Fields must have unique name')
        if primary_key_name:
            if primary_key_name not in title_set:
                raise ValueError('There are no fields with the title '
                                 'corresponding to the primary_key_name '
                                 f'({primary_key_name}).')
        self.name = name
        self.fields = args
        if primary_key_name:
            primary_key_field = next(filter(
                lambda field: field.name == primary_key_name, args))
            if not isinstance(primary_key_field, (ComposedField, SimpleField)):
                raise ModelInitException(f'The primary key must refer to '
                                         f'either a SimpleField or a '
                                         f'ComposedField')
            if isinstance(primary_key_field, ComposedField):
                for f in primary_key_field.meta_model.fields:
                    if not isinstance(f, SimpleField):
                        raise ModelInitException(
                            f'Primary key fields with non SimpleField fields '
                            f'are not supported.')
            self.fields = self.fields
            self.primary_key_field = primary_key_field

        MetaModel.modelClasses[self.name] = self._generate_class()
        ps.log.debug(f'A new meta model has been created. [{self.name}]')

    def __call__(self, name: str = None):
        """ Returns a ComposedField created from the fields of the MetaModel.
        """
        if not name:
            name = str.lower(self.name[0]) + self.name[1:]
        return ComposedField(name, meta_model=self)

    def get_class(self):
        """ Returns the class representing the model described by the MetaModel.

        Returns:
            The class stored in the modelClasses dict identified by name as key.
        """
        return MetaModel.modelClasses.get(self.name)

    def _generate_class(self):
        """ Generate the class based on the fields of the meta model.
        """

        def new(cls, *args, **kwargs):
            """ Create and return a new instance of the model.

            Attributes:
                args: A sequence of the values used to initialize the
                    class generated from the MetaModel
                kwargs: Values used to initialize the class generated form the
                    MetaModel with keywords

            Raises:
                ModelInitException:
                    If too many args are passes.
                    If an unknown key is present in kwargs.
                    If there are some inconsistencies between args and kwargs.
                    If the default type if wrong.
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

            ordered_fields = sorted(
                self.fields,
                key=lambda field: isinstance(field, ConditionalField))
            for field in ordered_fields:
                value = field_values.get(field.name)
                if not value:
                    if field.default is not None:
                        if callable(field.default):
                            value = field.default()
                        else:
                            value = copy.deepcopy(field.default)
                        if not isinstance(value, field.field_type):  # TODO
                            raise ModelInitException(
                                f'The default value has a bad type '
                                f'{type(value)}.Expected '
                                f'{field_values.field_type}'
                            )
                        field_values[field.name] = value
                    else:
                        field_values[field.name] = None  # TODO optional removed TEST
                else:
                    # In this case, the initialization depends on a condition
                    if isinstance(field, ConditionalField):
                        value = (
                            value,
                            field_values.get(field.evaluation_field_name))
                    field_values[field.name] = field.init_value(value)

            instance = super(cls, cls).__new__(cls)  # TODO

            for k, v in field_values.items():
                setattr(instance, k, v)

            return instance

        return type(self.name, (object,), {
            '__new__': new
        })

    def validate_id(self, **kwargs):
        """ This method is used to validate value which identifies the model
                through the primary key.

        Attributes:
            kwargs: If the keys are more than 1. They must match the name
                of the fields of the primary key. Values must match the types.

        Returns:
            It could be:
                - An instance of the related MetaModel if the primary_key
                    field is a ComposedField.
                - The value of the dict if the primary_key_field is a
                    SimpleField.
        """
        pkf = self.primary_key_field
        kwargs_len = len(kwargs.items())
        if isinstance(pkf, ComposedField) and \
                len(pkf.meta_model.fields) == kwargs_len:
            field_values = {
                k[0].name: k
                for k in zip(pkf.meta_model.fields, kwargs.values())}
            for k, v in field_values.items():
                field_values[k] = v[0].init_value(v[1], strict=False)  # TODO docs
            res_id = pkf.meta_model.get_class()(**field_values)
        elif isinstance(pkf, SimpleField) and kwargs_len == 1:
            res_id = list(kwargs.values())[0]
            res_id = pkf.init_value(res_id, strict=False)
            # TODO non String field breaks here? TEST!!
        else:
            raise ModelInitException('The primary key is not compatible.'
                                     f'{pkf}')
        return res_id

    def __repr__(self):
        return '<MetaModel {}:{}>'.format(self.name, self.fields)


class SimpleField(Field):
    """A SimpleField is Field with a static build in field_type.

    Class attributes:
        static_field_type (type): The static type of the Field.

    """
    static_field_type = None

    def __init__(self,
                 name: str,
                 default: Union[static_field_type,
                                Callable[..., static_field_type], None] = None) -> None:
        super().__init__(name, self.__class__.static_field_type,
                         default)

    # TODO docs
    def init_value(self, value, strict=True):
        if not strict:
            try:
                value = self.static_field_type(value)
            except Exception:  # TODO
                pass  # TODO
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

    def init_value(self, value, strict=True):
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

    This class inherits from Field.
    If a ComposedField is initialized through a MetaModel __call__ method,
        the field_type is already cached on MetaModel.modelClasses.
    The field_type is obtained from the MetaModel.
    """
    _FieldType = NewType('_FieldType', Field)

    def __init__(self,
                 name: str,
                 *args: Field,
                 meta_model: MetaModel = None) -> None:
        """ Initialize the ComposedField.

        Attributes:
            *args (Sequence[MetaModel._FieldType]): The fields which compose the
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


class ListField(Field):
    """ A list field.
    """

    def __init__(self,
                 name: str,
                 data_type: Union[SimpleField.__class__, MetaModel],
                 default: Union[list, Callable[..., list], None] = None) -> None:
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

    def init_value(self, value):
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

    def init_value(self, value):
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
