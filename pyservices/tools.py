import falcon
from multiprocessing import Process

from wsgiref import simple_server

import pyservices as ps

from pyservices import entity_codecs
from pyservices.layer_supertypes import Service
from pyservices.frameworks import FalconResourceCollection, FalconResource


# TODO abstract mode (many service types has server and client)
# TODO work on robustness!!! IMPORTANT
# TODO put this inside Service?
def rest_server(service: Service):
    """Given a Service, generates the RESTful gateway.

    Args:
        service (type): Service to be accessed by the gateway.
        conf (dict): Configuration of the restfullization (r13n). TODO remove
    """
    port = service.config.get('port') or 7890
    address = service.config.get('address') or 'localhost'
    framework = service.config.get('framework') or 'falcon'
    methods = set(filter(lambda m: hasattr(m, 'rest_interface'),
                         entity_codecs.instance_methods(service)))  # TODO rest_interface approach...
    uris = {m.rest_interface['uri'] for m in methods}
    resources_methods = {res: list(filter(
        lambda m: m.rest_interface['uri'] == res, methods))
        for res in uris}
    base_path = type(service).base_path
    # TODO refactor this
    # FIXME webserver
    if framework == ps.frameworks.FALCON:
        app = application = falcon.API()
        resources = {}
        for uri, methods in resources_methods.items():
            res = FalconResource(methods, )
            res_coll = FalconResourceCollection(methods)

            resources[uri] = res_coll
            resources[uri + '/{res_id}'] = res
        for uri, r in resources.items():
            path = f'/{base_path}/{uri}'
            app.add_route(path, r)
        httpd = simple_server.make_server(address, port, application)
        p = Process(target=httpd.serve_forever)
        # FIXME no Process
        p.start()
        return p, httpd


def rest_client(service: Service):
    # TODO
    pass
