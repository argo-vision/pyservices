import abc
import datetime
import json
from typing import Union

from pyservices.exceptions import MetaTypeException
from . import http_content_types
from .data_descriptors import MetaModel, ListField, ComposedField, \
    ConditionalField, DictField, SimpleField


def instance_attributes(inst):
    """Given an instance, lists the name of all public non-callable members.

    Attributes:
        inst (obj):  The instance of the object.
    """
    return [n for n in dir(inst)
            if not n.startswith('_')
            and not callable(getattr(inst, n))]


def instance_callable_objects(inst):
    """Given an instance, lists the public callable members.

    Attributes:
        inst (obj):  The instance of the object.
    """
    return [getattr(inst, n) for n in dir(inst)
            if not n.startswith('_')
            and callable(getattr(inst, n))]


def instance_to_dict_repr(val: object):
    """Recursively generates a dict (or a list of dict).

    Attributes:
        val (object):  The instance of the object.
    """

    # Single object
    if isinstance(val, (dict, bool, str, int, float, datetime.datetime)):
        return val

    # List of objects
    if isinstance(val, list):
        return [instance_to_dict_repr(el) for el in val]

    # Recursive encoding:
    return {k: instance_to_dict_repr(getattr(val, k))
            for k in instance_attributes(val)}


# TODO refactor
def dict_repr_to_instance(val: Union[dict, list], meta_model: MetaModel):
    """Recursively recreates an instance given the MetaModel.

    Attributes:
        val (Union[dict, list]): The representation of the data in text form
            with test form values
        meta_model (type): The MetaModel used to instantiate the object
    """

    # List of objects
    if isinstance(val, list):
        return [dict_repr_to_instance(el, meta_model) for el in val]

    # Single object
    for k in val.keys():
        t = next((field for field in meta_model.fields if field.name == k),
                 None)
        if isinstance(val[k], dict):
            # t is a DictField
            if isinstance(t, DictField):
                pass

            # t is a ComposedField
            elif isinstance(t, ComposedField):
                val[k] = dict_repr_to_instance(val[k], t.meta_model)

            # t is a ConditionalField
            elif isinstance(t, ConditionalField):
                condition = val.get(t.evaluation_field_name)
                if not condition or not t.meta_models.get(condition):
                    raise MetaTypeException("The MetaModel is not compatible "
                                            "with the given val.")
                val[k] = dict_repr_to_instance(val[k], t.meta_models.get(
                    condition))

            else:
                raise MetaTypeException("The MetaModel is not compatible with "
                                        "the given val.")

        # t is a ListField
        elif isinstance(val[k], list):
            if not isinstance(t, ListField):
                raise MetaTypeException("The MetaModel is not compatible "
                                        "with the given val.")
            if isinstance(t.data_type, MetaModel):
                val[k] = [dict_repr_to_instance(el, t.data_type)
                          for el in val[k]]
            elif issubclass(t.data_type, SimpleField):
                # constrains are applied to the ListField, here I create a
                # "permissive" temporary field used to initialize the values
                # of SimpleFields
                temporary_field = t.data_type('temporary_field')
                values = [temporary_field.init_value(v) for v in val[k]]
                val[k] = t.init_value(values)
            else:
                raise MetaTypeException("The MetaModel is not compatible "
                                        "with the given val.")
    # Instantiation:
    return meta_model.get_class()(**val)


class Codec(abc.ABC):
    """A base class for codecs.

    Class attributes:
        http_content_type (str): The content type of the related codec
    """

    http_content_type = None

    @classmethod
    @abc.abstractmethod
    def encode(cls, value):
        """Given a model object, returns its string
        representation in the http_content_type.

        Arguments:
            value (Model): A model instance.
        Returns:
            str: A string representing the model.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def decode(cls, value: str, meta_model: MetaModel):
        """Given a string representing the model,
        generates the model instance.

        Arguments:
            value (str): A string representing the model instance.
            meta_model (MetaModel): A MetaModel used to create the instance.
        Returns:
            Model: The model instance.
        """
        pass


class JSON(Codec):
    """A codec for the JSON format.
    """

    http_content_type = http_content_types.APPLICATION_JSON

    @classmethod
    def encode(cls, value):
        return json.dumps(instance_to_dict_repr(value), default=str)

    @classmethod
    def decode(cls, value: str, meta_model: MetaModel):
        return dict_repr_to_instance(json.loads(value), meta_model)
