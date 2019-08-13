import copy
import inspect

from typing import Optional

import pyservices as ps


class MetaModel:
    """ A class which represents the description of the model.

    Class attributes:
        modelClasses (dict): A static dict used to store the generated classes.
    """
    modelClasses = dict()

    def __init__(self,
                 name: str,
                 *args,
                 primary_key_name: Optional[str] = None) -> None:
        """ Initialize the meta model.

        Args:
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

            Args:
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
                        if not isinstance(value, field.field_type):
                            raise ModelInitException(
                                f'The default value has a bad type '
                                f'{type(value)}.Expected '
                                f'{field_values.field_type}'
                            )
                        field_values[field.name] = value
                    else:
                        field_values[field.name] = None
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
            '__new__': new,
            '__eq__': _meta_model_equality
        })

    def validate_id(self, **kwargs):
        """ This method is used to validate value which identifies the model
                through the primary key.

        Args:
            kwargs: If the keys are more than 1. They must match the name
                of the fields of the primary key. Values must match the types.

        Returns:
            It could be:
                - An instance of the related MetaModel's class if the
                    primary_key field is a ComposedField.
                - The value of the single kwarg passed if the primary_key_field
                    is a SimpleField.
        """
        pkf = self.primary_key_field
        kwargs_len = len(kwargs.items())
        if isinstance(pkf, ComposedField) and \
                len(pkf.meta_model.fields) == kwargs_len:
            field_names = [f.name for f in pkf.meta_model.fields]
            field_values = dict(zip(field_names, kwargs.values()))
            pkf.init_value(field_values, strict=False)
            res_id = pkf.meta_model.get_class()(**field_values)
        elif isinstance(pkf, SimpleField) and kwargs_len == 1:
            res_id = list(kwargs.values())[0]
            res_id = pkf.init_value(res_id, strict=False)
        else:
            raise ModelInitException('The primary key is not compatible.'
                                     f'{pkf}')
        return res_id

    def __repr__(self):
        return '<MetaModel {}:{}>'.format(self.name, self.fields)


def _meta_model_equality(self, other):
    if not isinstance(other, type(self)):
        return False
    from pyservices.data_descriptors.entity_codecs import instance_attributes
    fields = instance_attributes(self)
    for f in fields:
        if getattr(self, f) != getattr(other, f):
            return False
    return True


from pyservices.data_descriptors.fields import *
