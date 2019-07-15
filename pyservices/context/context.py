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

import importlib

from pyservices.exceptions import ComponentNotFoundException


class Context:
    def __init__(self):
        self._state = dict()
        self._startup_functions = []
        self.APP_KEY = "APP"

    def register(self, key, component):
        self._state[key] = component

    def register_app(self, app):
        self._state[self.APP_KEY] = app

    def get_app(self ):
        return self._state[self.APP_KEY]

    def register_startup(self, function: callable):
        self._startup_functions.append(function)

    def check_component_is_registered(self, key):
        try:
            self.get_component(key)
            return True
        except ComponentNotFoundException:
            return False

    def get_component(self, key):
        try:
            return self._state[key]
        except Exception:
            raise ComponentNotFoundException()

    def startup(self):
        for function in self._startup_functions:
            function(self)


def _compose(ctx: Context, components: list, registered: list):
    """
    :param ctx: context of the implementation
    :param components: list of components to be added

    For each component, it launch its registration function as well as the
    registration function of its
    COMPONENT DEPENDENCIES
    """

    if components is None or len(components) == 0:
        return

    component = components.pop()

    if component not in registered:
        module = importlib.import_module(component)
        dependencies: list = module.COMPONENT_DEPENDENCIES
        _compose(ctx, dependencies, registered)
        module.register_component(ctx)
        registered.append(component)
    _compose(ctx, components, registered)
    return


def create_application(conf):
    ctx = Context()
    _compose(ctx, conf['components'], [])
    ctx.startup()
    return ctx.get_app()

