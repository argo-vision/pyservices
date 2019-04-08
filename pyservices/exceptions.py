import pyservices as ps


# TODO is it good to log exceptions?
class PyservicesBaseException(Exception):
    """ Base exceptions for the module.
    """
    def __init__(self, msg):
        ps.log.exception(f'Trowing an Exception({type(self)}) - {msg})')
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


class HTTPExceptions(PyservicesBaseException):
    pass


class HTTPUnexpectedStatusCode(HTTPExceptions):
    def __init__(self, status_code):
        super().__init__(f'Unexpected status code: {status_code}.')


class HTTPNotFound(HTTPExceptions):
    def __init__(self):
        super().__init__(f'Resource not found.')
