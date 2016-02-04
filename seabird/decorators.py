from __future__ import absolute_import

from .utils import optional_args


class CallbackMetadata:
    def __init__(self):
        self.commands = []
        self.events = []


class CommandMetadata:
    def __init__(self, name, short_help, full_help):
        self.name = name
        self.short_help = short_help
        self.full_help = full_help

    def __repr__(self):
        return '<CommandMetadata: %s>' % self.name


def ensure_callback_metadata(callback):
    if getattr(callback, "_sb_meta", None) is None:
        callback._sb_meta = CallbackMetadata()

    return callback


@optional_args
def command(callback, name=None, short_help=None, full_help=None):
    """Register a function to be used as a command event handler

    This decorator takes the name of the command, the single line help
    and the extended help.

    If short_help and full_help are unused, it will attempt to pull
    this information from the function's docstring.
    """
    ensure_callback_metadata(callback)

    if name is None:
        name = callback.__name__

    # This portion is roughly based off of pydoc.splitdoc.  Note that
    # we only pull from the __doc__ string if both short_help and
    # long_help are None.
    if (short_help is None and
            full_help is None and
            callback.__doc__ is not None):
        lines = callback.__doc__.strip().splitlines()
        if len(lines) == 1:
            short_help = lines[0]
        elif len(lines) >= 2 and not lines[1].rstrip():
            short_help = lines[0]
            full_help = ' '.join(lines[2:])
        else:
            full_help = ' '.join(lines)

    # Now that we have the metadata, actually add it to the command list.
    callback._sb_meta.commands.append(
        CommandMetadata(name, short_help, full_help))

    return callback


def event(first, *args):
    """Register a function to be used as a raw event handler

    This function takes the names of one or more IRC events and
    returns a decorator which will add metadata to functions which is
    used for plugin initialization.
    """
    def decorator(callback):
        ensure_callback_metadata(callback)

        # Make sure all the metadata gets added.
        callback._sb_meta.events.append(first)
        for arg in args:
            callback._sb_meta.events.append(arg)

        return callback

    return decorator
