import abc
import json

from . import content_types
from .layer_supertypes import Model


def get(inst, memb):
    """
    Given an instance and a member name, returns it.
    """
    return inst.__getattribute__(memb)


def instance_attributes(inst):
    """
    Given an instance, lists the public non-callable members.
    """
    return [n 
        for n in dir(inst) 
        if not n.startswith('_') 
            and not callable(get(inst,n))
    ]


def instance_to_dict(val: Model):
    """
    Recursively generates a dictionary with builtins only.
    """
    # TODO: Check unsupported types.
    # TODO: Manage builtins.
    if type(val) == str: return val

    # Recursive encoding:
    return {k: instance_to_dict(get(val, k))
        for k in instance_attributes(val)
    }


def dict_to_instance(val: dict, model: type):
    """
    Recursively recreates an instance.
    """
    try:
        subtypes = model.subtypes
    except AttributeError:
        subtypes = {}  # TODO tmp

    for k in val.keys():
        t = subtypes.get(k)
        if type(val[k]) == dict and t:
            val[k] = dict_to_instance(val[k], t)

    # Instantiation:
    return model(**val)
    

class Codec(abc.ABC):
    """
    A base class for codecs.
    """

    @abc.abstractmethod
    def content_type(self):
        """
        The content-type managed by this codec.
        """
        pass

    @abc.abstractmethod
    def encode(self, value: Model):
        """
        Given a model object, returns its string 
        representation in the content_type.

        :model:     A model instance.
        :return:    A string representing the model.
        """
        pass

    @abc.abstractmethod
    def decode(self, value: str, model: type):
        """
        Given a string representing the model, 
        generates the model instance.

        :return:    A model instance.
        :model:     A string representing the model.
        """
        pass


class JSON(Codec):
    """
    A codec for the JSON format.
    """

    def content_type(self):
        return content_types.APPLICATION_JSON

    def encode(self, value: Model):
        return json.dumps(instance_to_dict(value))

    def decode(self, value: str, model: type):
        dict_to_instance(json.parse(value))

