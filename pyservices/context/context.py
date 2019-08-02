"""
Tool to manage the:
 1. composition of the micro-service as a stack of COMPONENTS,
 2. management of component dependencies,
 3. startup of the micro-service using the generated WSGI application.

Each component has a COMPONENT_KEY, a COMPONENT_DEPENDENCIES, and implements a
register_component function.

def register_component(ctx: Context):
    pass

register_component implements the initialization of the component. A component
can add a variable to the context using
ctx.register(COMPONENT_KEY, value).

A component can check if it's already registered with
ctx.check_component_is_registered(COMPONENT_KEY)

A component can add a function to the startup functions list using
ctx.register_startup.
Functions to be registered must receive context as argument.

One and no more then one component of the stack must call ctx.register_app to
register a WSGI interface to the context,
e.g.

def register_component(ctx: Context):
    if not ctx.check_component_is_registered(COMPONENT_KEY):
        app = falcon.API()
        ctx.register_app(app)

Gianluca Scarpellini - gianluca.scarpellini@argo.vision
"""
from pyservices.service_descriptors.proxy import create_service_connector
from pyservices.utilities.exceptions import ComponentNotFound
from pyservices.service_descriptors.layer_supertypes import Service


class Context:
    def __init__(self):
        self._state = dict()
        self._startup_functions = []
        self.APP_KEY = "APP"
        self._state[self.APP_KEY] = None

    def register(self, key, component):
        if isinstance(component, Service):
            create_service_connector(component.__class__, component)
        else:
            self._state[key] = component

    def register_app(self, app):
        self._state[self.APP_KEY] = app

    def get_app(self):
        return self._state[self.APP_KEY]

    def register_startup(self, function: callable):
        self._startup_functions.append(function)

    def check_component_is_registered(self, key):
        try:
            self.get_component(key)
            return True
        except ComponentNotFound:
            return False

    def get_component(self, key):
        try:
            return self._state[key]
        except Exception:
            raise ComponentNotFound('Cannot find {}'.format(key))

    def get_services(self):
        return {k: v for k, v in self._state.items() if isinstance(v, Service)}

    def startup(self):
        for function in self._startup_functions:
            function(self)
