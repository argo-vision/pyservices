import os
from typing import List


class MicroServicesConfiguration:
    """
    MicroServiceConfiguration

    """

    def __init__(self, configuration: dict):
        self.conf = configuration

    def current_microservice_name(self) -> str:
        """
            service name from os variable GAE_SERVICE
        """
        service: str = os.environ.get("GAE_SERVICE")
        return service.lower()

    def microservices_names(self) -> List[str]:
        return list(self.conf.keys())

    def microservice_address(self, microservice_name) -> str:
        microservice = self.conf.get(microservice_name)
        if microservice is None:
            raise ValueError("Micro service not found")

        return "{}:{}".format(microservice["address"], microservice["port"])

    def microservice_of(self, service: str) -> str:
        for micro in self.microservices_names():
            if service in self.microservice_services(micro):
                return micro
        raise ValueError("Service not found")

    def service_address(self, service: str) -> str:
        micro = self.microservice_of(service)
        return self.microservice_address(micro)

    def microservice_services(self, micro_name: str) -> List[str]:
        micro = self.microservice_configuration(micro_name)
        return micro["components"]

    def microservice_configuration(self, micro_name: str) -> dict:
        micro = self.conf.get(micro_name)
        if micro is None:
            raise ValueError("Micro service not found")
        return micro
