from typing import NamedTuple

from pyservices.service_descriptors.interfaces import InterfaceOperationDescriptor


class HTTPRequest(NamedTuple):
    """
    Descriptor of a HTTP request.
    """
    body: str = None
    query_params: dict = None


class HTTPResponse(NamedTuple):
    """
    Descriptor of a HTTP response.
    """
    status_code: int = None
    body: str = None


def get_updated_response(call: InterfaceOperationDescriptor, body: str) -> HTTPResponse:
    r = HTTPResponse()
    if body is not None:
        r = HTTPResponse(None, call.encoder.encode(body))
    return r


def get_data_from_request(call: InterfaceOperationDescriptor, req: HTTPRequest, **kwargs):
    has_meta_model = hasattr(call.interface, 'meta_model')
    ret = {}
    if kwargs:
        # The only kwargs supported are the auto-generated for single
        # resource operation, kwargs represent id
        if not has_meta_model:
            raise Exception  # TODO
        if hasattr(call.interface.meta_model, 'primary_key_field'):
            ret['res_id'] = call.interface.meta_model.validate_id(**kwargs)

    if call.decoder and call.http_method in ("put", "post"):
        # Expects some data
        data = req.body
        if data and has_meta_model:
            # Data has a specific shape
            ret['resource'] = (call.decoder.decode(
                data, call.interface.meta_model))
        elif data:
            # Data hasn't a specific shape
            d = call.decoder.decode_unshaped(data)
            if isinstance(d, dict):
                ret.update(d)
            else:
                # Only dict as non shaped is supported
                raise NotImplementedError()
    elif call.http_method == "get" and req.query_params:
        # Data, if present, is placed on request param
        ret.update(req.query_params)

    return ret

