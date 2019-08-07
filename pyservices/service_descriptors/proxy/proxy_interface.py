import abc
import inspect


class EndPoint(abc.ABC):
    def _merge_endpoints(self, *args):
        for arg in args:
            if not issubclass(type(arg), EndPoint):
                raise Exception  # FIXME too general

            methods = inspect.getmembers(arg)  # methods and attributes
            for (n, m) in methods:
                if not n.startswith('_'):
                    setattr(self, n, m)

