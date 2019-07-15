import abc

# TODO make a module
from pyservices.data_descriptors.entity_codecs import JSON


class InterfaceBase(abc.ABC):
    """Base class of interfaces.

    The methods of the class can be overloaded in a service implementation.
    """

    def __init__(self, service):
        self.service = service


class RestResource(InterfaceBase):
    """Restful interface of a single Resource.

    """
    meta_model = None
    resource_path = None
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
    def get_resource_name(cls):
        return cls.resource_path or f'{cls.meta_model.name.lower()}s'


class MessageInterface(InterfaceBase):
    # TODO
    pass
