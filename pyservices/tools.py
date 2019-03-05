import falcon
from multiprocessing import Process

from wsgiref import simple_server

import pyservices as ps

from pyservices.layer_supertypes import Service
from pyservices import entity_codecs


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


# TODO refactor
class FalconResourceCollection:
    def __init__(self, methods):
        self.add_method = next(
            filter(lambda m: m.rest_interface['operation'] == 'add',
                   methods), None)
        self.list_method = next(
            filter(lambda m: m.rest_interface['operation'] == 'list',
                   methods), None)

    def on_get(self, req, resp):
        try:
            if self.list_method:
                resp.body = self.list_method.rest_interface['produces'].encode(
                    self.list_method()
                )
            else:
                resp.status = falcon.HTTP_404
        except Exception:  # TODO
            raise Exception

    def on_put(self, req, resp):
        try:
            if self.add_method:
                resource = self.add_method.rest_interface['consumes'].decode(
                    req.stream.read(),
                    self.add_method.rest_interface['resource_meta_model'],
                )
                self.add_method(resource)
                resp.status = falcon.HTTP_CREATED
            else:
                resp.status = falcon.HTTP_404
        except Exception:  # TODO
            raise Exception


# TODO refactor
class FalconResource:
    def __init__(self, methods):
        self.update_method = next(
            filter(lambda m: m.rest_interface['operation'] == 'update',
                   methods), None)
        self.delete_method = next(
            filter(lambda m: m.rest_interface['operation'] == 'delete',
                   methods), None)
        self.detail_method = next(
            filter(lambda m: m.rest_interface['operation'] == 'detail',
                   methods), None)

    def on_get(self, req, resp, res_id):
        try:
            if self.detail_method:
                resp.body = self.detail_method.rest_interface['produces'].encode(
                    self.detail_method(res_id)
                )
            else:
                resp.status = falcon.HTTP_404
        except Exception:  # TODO
            raise Exception

    def on_post(self, req, resp, res_id):
        try:
            if self.update_method:
                resource = self.update_method.rest_interface['consumes'].decode(
                    req.stream.read(),
                    self.update_method.rest_interface['resource_meta_model'],
                )
                self.update_method(res_id, resource)
            else:
                resp.status = falcon.HTTP_404
        except Exception:  # TODO
            raise Exception

    def on_delete(self, req, resp, res_id):
        try:
            if self.delete_method:
                self.delete_method(res_id)
                # TODO http status
            else:
                resp.status = falcon.HTTP_404
        except Exception:  # TODO
            raise Exception

