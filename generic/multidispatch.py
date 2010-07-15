""" Multidispatch for functions."""

import functools
import inspect

from generic.registry import Registry
from generic.registry import TypeAxis

__all__ = ["Dispatcher", "multimethod", "reset"]

# function name -> dispatcher
dispatchers = {}


def multimethod(*arg_types):
    """ Declare function as multimethod."""
    global dispatchers
    def register_rule(func):
        argspec = inspect.getargspec(func)
        if func.__name__ in dispatchers:
            dispatcher = dispatchers[func.__name__]
        else:
            dispatcher = functools.wraps(func)(
                Dispatcher(argspec, len(arg_types)))
            dispatchers[func.__name__] = dispatcher
        dispatcher.register_rule(func, *arg_types)
        return dispatcher
    return register_rule


def reset():
    """ Reset dispatchers. Useful for testing."""
    global dispatchers
    dispatchers = {}


class Dispatcher(object):
    """ Function call dispatcher based on argument types."""

    def __init__(self, argspec, multi_arity):
        """ Initialize dispatcher with ``argspec`` of type
        :class:`inspect.ArgSpec` and ``multi_arity`` that represent number
        params."""
        pos_arity = \
            len(argspec.args if argspec.args else []) - \
            len(argspec.defaults if argspec.defaults else [])
        if pos_arity < multi_arity:
            raise TypeError("Not enough positional arguments "
                            "for number of type parameters provided.")
        self.argspec = argspec
        self.multi_arity = multi_arity
        axis = [("arg_%d" % n, TypeAxis()) for n in range(multi_arity)]
        self.registry = Registry(*axis)

    def register_rule(self, rule, *arg_types):
        """ Register new ``rule`` for ``arg_types``."""
        # Check if we have the right number of parametrized types 
        if len(arg_types) != self.multi_arity:
            raise TypeError("Wrong number of type parameters.")

        # Check if we have the same argspec (by number of args)
        argspec = inspect.getargspec(rule)
        if not map(lambda x: len(x) if x else 0, argspec) == \
          map(lambda x: len(x) if x else 0, self.argspec):
            raise TypeError("Rule does not conform "
                            "to previous implementations.")

        self.registry.register(rule, *arg_types)

    def lookup_rule(self, *args):
        """ Lookup rule by ``args``. Returns None if no rule was found."""
        return self.registry.lookup(*args[:self.multi_arity])

    def __call__(self, *args):
        """ Dispatch call to appropriate rule."""
        rule = self.lookup_rule(*args)
        if rule is None:
            raise TypeError("No avaible rule found for %r" % (args,))
        return rule(*args)
