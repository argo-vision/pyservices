import pyservices as ps


# TODO rename with Error/Exception in every name
class PyservicesBaseException(Exception):
    """ Base exceptions for the module.
    """
    def __init__(self, msg):
        # ps.log.exception(f'Trowing an Exception({type(self)}) - {msg})') TODO make oneline!
        super().__init__(msg)


class ModelInitException(PyservicesBaseException):
    """Error initializing the MetaModel.
    """
    pass


class CodecException(PyservicesBaseException):
    """ Error on a Codec."""
    pass


class ServiceException(PyservicesBaseException):
    """General error on Service.
    """
    pass


class ClientException(ServiceException):
    """General error on a client.
    """
    pass


class InterfaceDefinitionException(ServiceException):
    """Error generating the interface of the service.
    """
    pass


class MetaTypeException(PyservicesBaseException):
    """Error while using the wrong MetaModel type.
    """
    pass


class HTTPException(ServiceException):
    """Error related to HTTP protocol.
    """
    pass


class HTTPUnexpectedStatusCode(HTTPException):
    def __init__(self, status_code):
        super().__init__(f'Unexpected status code: {status_code}.')


class HTTPNotFound(HTTPException):
    def __init__(self):
        super().__init__(f'Resource not found.')


class ComponentNotFound(PyservicesBaseException):
    pass


class ServiceNotFound(PyservicesBaseException):
    pass


class MicroserviceConfigurationError(PyservicesBaseException):
    pass


class ServiceDependenciesError(PyservicesBaseException):
    pass
