import unittest

from pyservices.context.dependencies import create_application
from pyservices.context.dependencies import microservice_sorted_dependencies, \
    components_graph, topological_sort, is_acyclic
from pyservices.context.microservice_utils import MicroServiceConfiguration
from pyservices.service_descriptors.WSGIAppWrapper import WSGIAppWrapper
from pyservices.utils.exceptions import MicroServiceConfigurationError, \
    ServiceDependenciesError
from test.context.components.configuration import configurations


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

    def testMicroServiceDependencies(self):
        deps = microservice_sorted_dependencies(
            configurations['micro-service1']['services'])
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
        conf = MicroServiceConfiguration(configurations, 'micro-service-circular')
        self.assertRaises(ServiceDependenciesError, create_application, conf)

    def testComponentGraph(self):
        graph = components_graph({},
                                 configurations['micro-service1']['services'][0])
        from test.context.components.service1 import COMPONENT_KEY as key
        from test.context.components.service1 import COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)
        graph = components_graph({},
                                 configurations['micro-service1']['services'][
                                     1])
        from test.context.components.service2 import COMPONENT_KEY as key
        from test.context.components.service2 import \
            COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)

    def testCreateApplication(self):
        conf = MicroServiceConfiguration(configurations, 'micro-service1')
        app = create_application(conf)
        self.assertTrue(isinstance(app, WSGIAppWrapper))
        conf = MicroServiceConfiguration(configurations, 'micro-service2')
        app = create_application(conf)
        self.assertTrue(isinstance(app, WSGIAppWrapper))
