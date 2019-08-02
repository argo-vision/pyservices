import logging

logger = logging.getLogger(__package__)


def local_request_call(interface, actual_method_name, local_data=None, **kwargs):
    try:
        method = getattr(interface, actual_method_name)
        data = method(**local_data)
    except Exception:
        # TODO
        raise Exception
    return data
