import abc
import json
import datetime

from typing import Union

from . import http_content_types
from .data_descriptors import MetaModel, SequenceField, ComposedField, \
    ConditionalField
from .layer_supertypes import Model


def get(inst, memb):
    """Given an instance and a member name, returns it.

    Attributes:
        inst (obj):  The instance of the object.
        memb (str): The name of the attribute.
    """

    return inst.__getattribute__(memb)


def instance_attributes(inst):
    """Given an instance, lists the name of all public non-callable members.

    Attributes:
        inst (obj):  The instance of the object.
    """
    return [n for n in dir(inst)
            if not n.startswith('_')
            and not callable(get(inst, n))]


def instance_callable_objects(inst):
    """Given an instance, lists the public callable members.

    Attributes:
        inst (obj):  The instance of the object.
    """
    return [get(inst, n) for n in dir(inst)
            if not n.startswith('_')
            and callable(get(inst, n))]


def instance_to_repr(val: object):
    """Recursively generates a dict (or a list of dict).

    Attributes:
        val (object):  The instance of the object.
    """

    # Single object
    if isinstance(val, (bool, str, int, float, datetime.datetime)):
        return val

    # List of objects
    if isinstance(val, list):
        return [instance_to_repr(el) for el in val]

    # Recursive encoding:
    return {k: instance_to_repr(get(val, k))
            for k in instance_attributes(val)}


# TODO refactor
def repr_to_instance(val: Union[dict, list], meta_model: type):
    """Recursively recreates an instance given the MetaModel.

    Attributes:
        val (Union[dict, list]): The representation of the data in text form
            with test form values
        meta_model (type): The MetaModel used to instantiate the object
    """

    # List of objects
    if isinstance(val, list):
        return [repr_to_instance(el, meta_model) for el in val]

    # Single object
    for k in val.keys():
        t = next((field for field in meta_model.fields if field.name == k),
                 None)
        # t is a ConditionalField
        # t is a ComposedField
        if isinstance(val[k], dict):
            if isinstance(t, ComposedField):
                val[k] = repr_to_instance(val[k], t.meta_model)
            elif isinstance(t, ConditionalField):
                condition = val.get(t.evaluation_field_name)
                if not condition or not t.meta_models.get(condition):
                    raise TypeError("The MetaModel is not compatible with the "
                                    "given val.")
                val[k] = repr_to_instance(val[k], t.meta_models.get(condition))
            else:
                raise TypeError("The MetaModel is not compatible with the "
                                "given val.")

        # t is a SequenceField
        elif isinstance(val[k], list):
            if not isinstance(t, SequenceField):
                raise TypeError("The MetaModel is not compatible with the "
                                "given val.")
            val[k] = [repr_to_instance(el, t.data_type.meta_model)
                      for el in val[k]]

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
    def encode(cls, value: Model):
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
    def encode(cls, value: Model):
        return json.dumps(instance_to_repr(value), default=str)

    @classmethod
    def decode(cls, value: str, meta_model: MetaModel):
        return repr_to_instance(json.loads(value), meta_model)
