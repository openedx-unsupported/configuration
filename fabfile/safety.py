from fabric.api import env

from output import notify

def noopable(fun):
    if env.noop:
        def noop(*args, **kwargs):
            notify("Would have called: {fun}({args}, {kwargs})".format(
                fun=fun.__name__,
                args=", ".join(repr(a) for a in args),
                kwargs=", ".join("=".join([key, repr(val)]) for key, val in kwargs.items()),
            ))
        return noop
    else:
        return fun
