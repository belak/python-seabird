import functools


def optional_args(func):
    """Wrap a decorator to take either 1 or multiple args

    This uses some magic to determine if there is only one arg and if
    it's callable. If it is, we simply call the decorator with no args
    aside from the callback.

    If there are any args given, they are meant as arguments to the
    decorator, so we wrap the decorator.
    """
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        # If we have 1 arg and it's callable, wrap it
        if len(args) == 1 and len(kwargs) == 0 and callable(func):
            return func(args[0])

        # If there's more than one arg, they're meant as args to the decorator
        # function, so we pass them through, along with the decorated func.
        def inner(user_func):
            return func(user_func, *args, **kwargs)

        return inner

    return func_wrapper
