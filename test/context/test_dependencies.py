import os
import unittest

import pyservices.context.microservice_utils as config_utils
from pyservices.context.dependencies import dependent_remote_components, dependent_components, \
    microservice_sorted_dependencies, topological_sort, is_acyclic, components_graph, create_application
from pyservices.utils.exceptions import MicroserviceConfigurationError, ServiceDependenciesError
from test.context.uservices import get_path


class TestDependencies(unittest.TestCase):
    _old_service_name = os.getenv("GAE_SERVICE")
    _old_config_dir = config_utils._config_dir
    _my_config_path = 'test.context.uservices'

    @classmethod
    def setUpClass(cls):
        os.environ["GAE_SERVICE"] = "MICROService1"
        config_utils._config_dir = cls._my_config_path

    @classmethod
    def tearDownClass(cls):
        if cls._old_service_name:
            os.environ["GAE_SERVICE"] = cls._old_service_name
        else:
            os.environ.pop("GAE_SERVICE")
        config_utils._config_dir = cls._old_config_dir

    def test_dependent_services(self):
        deps = dependent_components('microservice2')
        self.assertEqual({get_path('component2')}, deps)
        deps = dependent_components('microservice1')
        self.assertEqual({get_path('service2')}, deps)

    def test_dependent_remote_service(self):
        deps = dependent_remote_components('microservice2')
        self.assertEqual({get_path('component2')}, deps)
        deps = dependent_remote_components('microservice1')
        self.assertEqual(set(), deps)

    def testNullMicroservice(self):
        self.assertRaises(MicroserviceConfigurationError,
                          microservice_sorted_dependencies,
                          None)

    def testEmptyMicroservice(self):
        self.assertRaises(MicroserviceConfigurationError,
                          microservice_sorted_dependencies,
                          'micro_service_empty')

    def testMicroserviceWithNotRealComponent(self):
        self.assertRaises(MicroserviceConfigurationError,
                          microservice_sorted_dependencies,
                          'micro_service_broken')

    def testTopologicalSort(self):
        ts = ['pyservices.service_descriptors.WSGIAppWrapper',
              'test.context.components.service3',
              'test.context.components.component2',
              'test.context.components.component1',
              'test.context.components.service2',
              'test.context.components.service1']
        graph = {
            'test.context.components.service1': [
                'pyservices.service_descriptors.WSGIAppWrapper',
                'test.context.components.component1'],
            'test.context.components.component1': [
                'test.context.components.component2'],
            'test.context.components.component2': [
                'test.context.components.service3'],
            'test.context.components.service3': [
                'pyservices.service_descriptors.WSGIAppWrapper'],
            'pyservices.service_descriptors.WSGIAppWrapper': [],
            'test.context.components.service2': [
                'pyservices.service_descriptors.WSGIAppWrapper',
                'test.context.components.component1']}
        self.assertListEqual(topological_sort(graph), ts)

    def testMicroserviceDependencies(self):
        deps = microservice_sorted_dependencies('microservice1')
        expected = ['pyservices.service_descriptors.WSGIAppWrapper',
                    'test.context.components.service3',
                    'test.context.components.component2',
                    'test.context.components.component1',
                    'test.context.components.service1',
                    'test.context.components.service2']
        self.assertListEqual(deps, expected)

    def testAcyclicGraph(self):
        cyclic = {'A': ['B'], 'B': ['C'], 'C': ['A']}
        self.assertFalse(is_acyclic(cyclic))
        acyclic = {'A': ['B'], 'B': ['C'], 'C': []}
        self.assertTrue(is_acyclic(acyclic))

    def testAcyclicGraph2(self):
        acyclic = {'S1': ['C1', 'F'], 'C1': ['C2'], 'C2': ['S3'], 'S2': ['F', 'C1', 'S1'], 'F':[]}
        self.assertTrue(is_acyclic(acyclic))

    # NOTE: this is commented because is false
    # TODO(a-tomasi):
    #   - if the test makes no sense just remove it
    #   - if the test doesn't do what it does just fix it
    #   Some details:
    #   - for the initial phase of the project we made the, although strong, assumption
    #       that cyclic deps are not supported. Not many use cases will be affected by this
    #       temporary choice and certainly not project we are working in
    #   - when this assumption will fall and then the code will be adaped in a proper way
    #       we can remove the test, until then it's dangerous ignore tests
    #       without WELL EXPLAINED reasons.
    def ignored_testCyclicDeps(self):
        self.assertRaises(ServiceDependenciesError, create_application)

    def testComponentGraph(self):
        graph = components_graph({}, config_utils.services('microservice1')[0])
        from test.context.components.service1 import COMPONENT_KEY as key
        from test.context.components.service1 import COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)
        graph = components_graph({}, config_utils.services('microservice1')[1])
        from test.context.components.service2 import COMPONENT_KEY as key
        from test.context.components.service2 import \
            COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)
