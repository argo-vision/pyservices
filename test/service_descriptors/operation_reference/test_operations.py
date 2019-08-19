import os
import unittest

import pyservices.context.microservice_utils as config_utils
from pyservices.context.dependencies import create_application
from pyservices.service_descriptors.layer_supertypes import Service, ServiceOperationReference

Service._module_prefix = 'test.service_descriptors.components'


class TestOperations(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.service_descriptors.uservices'

    @classmethod
    def setUpClass(cls):
        os.environ["GAE_SERVICE"] = "micro-service1"
        config_utils._config_dir = cls._my_config_path

    @classmethod
    def tearDownClass(cls):
        if cls._old_service_name:
            os.environ["GAE_SERVICE"] = cls._old_service_name
        else:
            os.environ.pop("GAE_SERVICE")
        config_utils._config_dir = cls._old_config_dir

    def testReferenceOperations(self):
        app = create_application()
        reference = ServiceOperationReference("service1", "NotesOperation", "read_note")
        self.assertEqual(reference(), "My content")
