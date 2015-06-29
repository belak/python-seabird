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


def event(*args):
    def decorator(callback):
        ensure_callback_metadata(callback)

        for arg in args:
            callback._sb_meta.events.append(arg)

        return callback

    return decorator


def interval(interval):
    raise NotImplementedError


def mention(callback):
    raise NotImplementedError
