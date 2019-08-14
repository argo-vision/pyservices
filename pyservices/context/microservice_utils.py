import os
import importlib

from pyservices.context.dependencies import dependent_remote_components
from pyservices.utils.exceptions import MicroserviceConfigurationError

_config_dir = 'uservices'


def config_dict(config_package: str) -> dict:
    """
    Args:
        config_package (str): The package containing the configuration files

    Returns:
        A dictionary containing all the configurations
    """
    path = importlib.import_module(config_package).__path__[0]
    sub_modules = [p.replace('.py', '') for p in os.listdir(path)]
    config = {m: importlib.import_module(f'{config_package}.{m}').config
              for m in sub_modules if not m.startswith('_')}
    return config


def current_microservice() -> str:
    """
        Returns:
            The current micro-service name.
    """
    service = os.environ["GAE_SERVICE"]  # TODO #38
    return service.lower() if service is not None else ""


def current_config_path():
    current_ms = current_microservice()
    return f'{_config_dir}.{current_ms}'


def current_config():
    """
        Returns:
            The current micro-service configuration.
    """
    return config_dict(_config_dir)


def current_host():
    current_ms = current_microservice()
    return host(current_ms)


def host(service_microservice: str):
    """
    Args:
        # TODO hide name of module, use name of service (convention)
        service_microservice (str): could be the string of the module of the 
            service or the microservice_name
    Returns:
        The host of the microservice {address}:{port}
    """
    config = current_config()
    for ms, ms_config in config.items():
        if service_microservice == ms or service_microservice in ms_config['services']:
            address = ms_config["address"]
            port = ms_config["port"]
            return f'{address}:{port}'
    raise ValueError(f'There is not service or microservice matching the name: '
                     f'{service_microservice}')


def services(service_microservice: str) -> list:
    """
    Args:
        # TODO hide name of module, use name of service (convention)
        service_microservice (str): could be the string of the module of the
            service or the microservice_name    Returns:
        The services of microservice
    """
    config = current_config()
    try:
        microservice = microservice_name(service_microservice)
    except ValueError:
        microservice = service_microservice
    try:
        return config[microservice]['services']
    except KeyError as e:
        raise MicroserviceConfigurationError(e)


def all_services():
    services = []
    config = current_config()
    for ss in config.values():
        services.extend(ss['services'])
    return services


def microservice_name(service: str):
    config = current_config()
    for ms, config in config.items():
        if service in config['services']:
            return ms
    raise ValueError('Service not present')


def remote_dependent_components() -> set:
    """
    Returns:
        The remote components which depends on current_microservice
    """
    ms = current_microservice()
    return dependent_remote_components(ms)
