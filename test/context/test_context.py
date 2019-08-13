import unittest

from pyservices.context.dependencies import create_application
from pyservices.context.dependencies import microservice_sorted_dependencies, \
    components_graph, topological_sort, is_acyclic
import pyservices.context.microservice_utils as config_utils
from pyservices.service_descriptors.WSGIAppWrapper import WSGIAppWrapper
from pyservices.utils.exceptions import MicroserviceConfigurationError, \
    ServiceDependenciesError


class TestContext(unittest.TestCase):
    def testNullMicroservice(self):
        self.assertRaises(MicroserviceConfigurationError,
                          microservice_sorted_dependencies,
                          None)

    def testEmptyMicroservice(self):
        self.assertRaises(MicroserviceConfigurationError,
                          microservice_sorted_dependencies,
                          config_utils.services('micro_service_empty'))

    def testMicroserviceWithNotRealComponent(self):
        self.assertRaises(MicroserviceConfigurationError,
                          microservice_sorted_dependencies,
                          MicroserviceConfiguration('micro_service_broken'))

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
        deps = microservice_sorted_dependencies(
            MicroserviceConfiguration('microservice1'))
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
        conf = MicroserviceConfiguration('micro-service-circular')
        self.assertRaises(ServiceDependenciesError, create_application, conf)

    def testComponentGraph(self):
        graph = components_graph({},
                                 MicroserviceConfiguration('microservice1')
                                 .services()[0])
        from test.context.components.service1 import COMPONENT_KEY as key
        from test.context.components.service1 import COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)
        graph = components_graph({},
                                 MicroserviceConfiguration('microservice1')
                                 .services()[1])
        from test.context.components.service2 import COMPONENT_KEY as key
        from test.context.components.service2 import \
            COMPONENT_DEPENDENCIES as deps
        self.assertEqual(graph[key], deps)

    def testCreateApplication(self):
        conf = MicroserviceConfiguration('microservice1')
        app = create_application(conf)
        self.assertTrue(isinstance(app, WSGIAppWrapper))
        conf = MicroserviceConfiguration('microservice2')
        app = create_application(conf)
        self.assertTrue(isinstance(app, WSGIAppWrapper))
