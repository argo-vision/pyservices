import copy
import functools
import importlib
import inspect

from pyservices.context import Context
from pyservices.service_descriptors.layer_supertypes import Service
from pyservices.service_descriptors.proxy import create_service_connector
from pyservices.utilities.exceptions import MicroServiceConfigurationError, \
    ServiceDependenciesError


def microservice_sorted_dependencies(services: list):
    if len(services) == 0:
        raise MicroServiceConfigurationError("Micro service configuration "
                                             "contains no services.")
    deps_graph = functools.reduce(components_graph, services, {})
    if not is_acyclic(deps_graph):
        raise ServiceDependenciesError('There are some cyclic dependencies')

    return topological_sort(deps_graph)


def get_service_class(module):
    services = [c[1] for c in inspect.getmembers(module)
                if inspect.isclass(c[1]) and issubclass(c[1], Service)
                and c[1] is not Service]
    dim = len(services)
    if dim == 0:
        return None
    elif dim == 1:
        return services[0]
    else:
        raise MicroServiceConfigurationError('A component module can contain'
                                             'at most one service.')


def topological_sort(graph):
    if not isinstance(graph, dict):
        raise TypeError('Graph must be a dict.')
    keys = graph.keys()
    if len(keys) == 0:
        raise ValueError('Graph is empty.')
    for k in keys:
        if not isinstance(graph[k], list):
            raise TypeError('Graph values must be lists.')
    edge = list(graph.keys()).pop()
    sort_graph = copy.deepcopy(graph)
    sorted_edges = []
    while True:
        search = []
        destructive_dfs(sort_graph, edge, search)
        sorted_edges = sorted_edges + search
        remaining = set(sort_graph.keys()).difference(sorted_edges)
        if not remaining:
            return sorted_edges
        else:
            edge = remaining.pop()


# FIXME module as string or "component"
def components_graph(graph, component):
    try:
        module = importlib.import_module(component)
        missing_nodes = module.COMPONENT_DEPENDENCIES.copy()
        graph.update({module.COMPONENT_KEY: missing_nodes.copy()})
        while len(missing_nodes):
            next_module = importlib.import_module(missing_nodes.pop())
            service = get_service_class(next_module)
            key = next_module.COMPONENT_KEY
            if service is not None and issubclass(service,Service):
                # No dependencies for a remote service
                graph[key] = []
                continue
            deps = next_module.COMPONENT_DEPENDENCIES.copy()
            if key not in graph.keys():
                missing_nodes.extend(deps)
                graph[key] = [importlib.import_module(d).COMPONENT_KEY
                              for d in deps]
        return graph
    except ModuleNotFoundError as e:
        raise MicroServiceConfigurationError(e.msg)


def is_acyclic(graph):
    test_graph = copy.deepcopy(graph)

    leaves_without_a_root = list(set(sum(test_graph.values(), [])) - set(test_graph.keys()))
    for l in leaves_without_a_root:
        test_graph[l] = []

    while test_graph:
        leaves = [edge for edge, adj in test_graph.items() if not adj]
        if not leaves:
            return False
        for leaf in leaves:
            for edge, adj in test_graph.items():
                try:
                    adj.remove(leaf)
                except ValueError as e:
                    pass
            if leaf in test_graph.keys():
                test_graph.pop(leaf)
    return True


def destructive_dfs(graph: dict, edge: str, visit: list):
    try:
        visit.index(edge)
    except ValueError:
        adj = graph[edge]
        for e in adj:
            if e in graph.keys():
                destructive_dfs(graph, e, visit)
        visit.append(edge)
        graph.pop(edge)


# FIXME move
def create_application(conf):
    ctx = Context()
    components = conf.sorted_dependencies()
    for dep in components:
        m = importlib.import_module(dep)
        service = get_service_class(m)
        if service is not None and dep not in conf.services():
            remote_service = create_service_connector(service,conf.address_of(dep))
            ctx.register(m.COMPONENT_KEY,remote_service)
        else:
            m.register_component(ctx)
    # _inject_dependencies(ctx.get_services(), conf) TODO connectors_injections
    ctx.startup()
    return ctx.get_app()


def _inject_dependencies(services, conf):
    remotes = {m: conf.address_of(s.__module__) if m not in conf.services() else 'local'
               for m, s in services.items()}

    for module, service in services.items():
        if remotes[module] == 'local':
            connectors = {s.service_base_path: create_service_connector(s.__class__, remotes[m])
                          for m, s in services.items()
                          if m in importlib.import_module(module).COMPONENT_DEPENDENCIES}
            [service.add_connector(bp, c) for bp, c in connectors.items()]
