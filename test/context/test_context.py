import unittest

from pyservices.context.dependencies import microservice_sorted_dependencies, \
    components_graph, topological_sort, is_acyclic
from pyservices.context.dependencies import create_application
from pyservices.utilities.exceptions import MicroServiceConfigurationError, \
    ServiceDependenciesError
from pyservices.service_descriptors.frameworks import FrameworkApp

from test.context.configuration import configurations


class TestContext(unittest.TestCase):
    def testNullMicroService(self):
        self.assertRaises(MicroServiceConfigurationError,
                          microservice_sorted_dependencies,
                          ['not-real-ms'])

    def testEmptyMicroService(self):
        self.assertRaises(MicroServiceConfigurationError,
                          microservice_sorted_dependencies,
                          configurations['micro-service-empty']['services'])

    def testMicroServiceWithNotRealComponent(self):
        self.assertRaises(MicroServiceConfigurationError,
                          microservice_sorted_dependencies,
                          configurations['micro-service-broken']['services'])

    def testTopologicalSort(self):
        ts = ['pyservices.service_descriptors.frameworks',
              'test.context.components.service3',
              'test.context.components.component2',
              'test.context.components.component1',
              'test.context.components.service2',
              'test.context.components.service1']
        graph = {
            'test.context.components.service1': [
                'pyservices.service_descriptors.frameworks',
                'test.context.components.component1'],
            'test.context.components.component1': [
                'test.context.components.component2'],
            'test.context.components.component2': [
                'test.context.components.service3'],
            'test.context.components.service3': [
                'pyservices.service_descriptors.frameworks'],
            'pyservices.service_descriptors.frameworks': [],
            'test.context.components.service2': [
                'pyservices.service_descriptors.frameworks',
                'test.context.components.component1']}
        self.assertListEqual(topological_sort(graph), ts)

    def testMicroServiceDependencies(self):
        deps = microservice_sorted_dependencies(
            configurations['micro-service1']['services'])
        expected = ['pyservices.service_descriptors.frameworks',
                    'test.context.components.service3',
                    'test.context.components.component2',
                    'test.context.components.component1',
                    'test.context.components.service2',
                    'test.context.components.service1']
        self.assertListEqual(deps, expected)

    def testAcyclicGraph(self):
        cyclic = {'A': ['B'], 'B': ['C'], 'C': ['A']}
        self.assertFalse(is_acyclic(cyclic))
        acyclic = {'A': ['B'], 'B': ['C'], 'C': []}
        self.assertTrue(is_acyclic(acyclic))

    def testCyclicDeps(self):
        self.assertRaises(ServiceDependenciesError, create_application,
                          configurations['micro-service-circular'])

    def testComponentGraph(self):
        graph = components_graph({},
                                 configurations['micro-service1']['services'][
                                     0])
        from test.context.components.service1 import COMPONENT_KEY as key
        from test.context.components.service1 import \
            COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)
        graph = components_graph({},
                                 configurations['micro-service1']['services'][
                                     1])
        from test.context.components.service2 import COMPONENT_KEY as key
        from test.context.components.service2 import \
            COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)

    def testCreateApplication(self):
        app = create_application(configurations['micro-service1'])
        self.assertTrue(isinstance(app, FrameworkApp))
        app = create_application(configurations['micro-service2'])
        self.assertTrue(isinstance(app, FrameworkApp))
