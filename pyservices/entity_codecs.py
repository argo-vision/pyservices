import abc
import json
import datetime

from . import content_types
from .data_descriptors import MetaModel
from .layer_supertypes import Model


def get(inst, memb):
    """Given an instance and a member name, returns it.
    """
    return inst.__getattribute__(memb)


def instance_attributes(inst):
    """Given an instance, lists the name of all public non-callable members.
    """
    return [n for n in dir(inst)
            if not n.startswith('_')
            and not callable(get(inst, n))]


def instance_methods(inst):
    """Given an instance, lists the public callable members.
    """
    return [get(inst, n) for n in dir(inst)
            if not n.startswith('_')
            and callable(get(inst, n))]


def instance_to_dict(val: Model):
    """Recursively generates a dictionary with builtins only.
    """
    # TODO: Extend the base types
    if isinstance(val, (bool, str, int, float, datetime.datetime)):
        return val
    if isinstance(val, list):
        return [instance_to_dict(el) for el in val]

    # Recursive encoding:
    return {k: instance_to_dict(get(val, k))
            for k in instance_attributes(val)}


def dict_to_instance(val: dict, meta_model: type):
    """Recursively recreates an instance given the MetaModel.
    """
    for k in val.keys():
        if isinstance(val[k], dict):
            t = next((field for field in meta_model.fields if field.name == k),
                     None)
            if not t:
                raise TypeError("The MetaModel is not compatible with the dict."
                                "\"{}\" key does not find the related field")
            val[k] = dict_to_instance(val[k], t)

    # Instantiation:
    return meta_model.get_class()(**val)


class Codec(abc.ABC):
    """A base class for codecs.
    """

    @classmethod
    @abc.abstractmethod
    def content_type(cls):
        """The content-type managed by this codec.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def encode(cls, value: Model):
        """Given a model object, returns its string
        representation in the content_type.

        Args:
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

        Args:
            value (str): A string representing the model instance.
            meta_model (MetaModel): A MetaModel used to create the instance.
        Returns:
            Model: The model instance.
        """
        pass


class JSON(Codec):
    """A codec for the JSON format.
    """

    @classmethod
    def content_type(cls):
        return content_types.APPLICATION_JSON

    @classmethod
    def encode(cls, value: Model):
        return json.dumps(instance_to_dict(value), default=str)

    @classmethod
    def decode(cls, value: str, meta_model: MetaModel):
        return dict_to_instance(json.loads(value), meta_model)
