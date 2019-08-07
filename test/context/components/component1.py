from pyservices.context import Context
from ..configuration import get_path

COMPONENT_DEPENDENCIES = [get_path('component2')]
COMPONENT_KEY = __name__


def register_component(ctx: Context):
    ctx.register(COMPONENT_KEY, None)
