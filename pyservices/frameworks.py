import falcon

# REST Framework
FALCON = 'Falcon'


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
