import os
from typing import List

from pyservices.context.dependencies import microservice_sorted_dependencies


class MicroServiceConfiguration:
    def __init__(self, conf: dict, name=None):
        if name is None:
            self.name = MicroServiceConfiguration._current_microservice_name()
        else:
            self.name = name
        if conf.get(self.name) is None:
            raise ValueError("Cannot find service")
        self.conf = conf

    def address(self) -> str:
        return self.microservice_address(self.name)

    def address_of(self, service: str) -> str:
        micro = self.microservice_of(service)
        return self.microservice_address(micro)

    def services(self) -> List[str]:
        return self.conf[self.name].get("services", [])

    def sorted_dependencies(self) -> List[str]:
        return microservice_sorted_dependencies(self.services())

    def microservices_names(self) -> List[str]:
        return list(self.conf.keys())

    @staticmethod
    def _current_microservice_name() -> str:
        """
            service name from os variable GAE_SERVICE
        """
        service = os.environ.get("GAE_SERVICE")
        return service.lower() if service is not None else ""

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

    def microservice_services(self, micro_name: str) -> List[str]:
        micro = self.microservice_configuration(micro_name)
        return micro.services()

    def microservice_configuration(self, micro_name: str):
        return MicroServiceConfiguration(self.conf, micro_name)
