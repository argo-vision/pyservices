import logging
import pyservices as ps


# TODO is it good to log exceptions?
class PyservicesBaseException(Exception):
    """ Base exceptions for the module.
    """
    def __init__(self, msg):
        logging.getLogger(ps.LOGGER_NAME).exception(f'Trowing an Exception'
                                                    f'({type(self)}) - {msg})')
        super().__init__(msg)


class ModelInitException(PyservicesBaseException):
    """Error initializing the MetaModel.
    """
    pass


class InterfaceDefinitionException(PyservicesBaseException):
    """Error generating the interface of the service.
    """
    pass


class MetaTypeException(PyservicesBaseException):
    """Error while using the wrong MetaModel type.
    """
    pass
