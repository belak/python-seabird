from collections import namedtuple


# CommandCallback is a simple class which contains the command
# metadata and the function relating to the command
CommandCallback = namedtuple('CommandCallback', ['meta', 'func'])


class PluginMetadata:
    def __init__(self, plugin):
        self.commands = {}
        self.events = {}

        for func_name in dir(plugin):
            func = getattr(plugin, func_name)
            if not hasattr(func, '_sb_meta'):
                continue

            # This is just because I don't want to keep referring to
            # it as func._sb_meta
            func_meta = func._sb_meta

            for command in func_meta.commands:
                if command.name in self.commands:
                    raise KeyError('Command %s already registered '
                                   'for this plugin' % command.name)

                self.commands[command.name] = CommandCallback(func_meta, func)

            for event in func_meta.events:
                if event not in self.events:
                    self.events[event] = []

                self.events[event].append(func)

    def dispatch_event(self, bot, event):
        for func in self.events.get(event.event, []):
            func(event)

    def dispatch_command(self, bot, cmd):
        if cmd.event in self.commands:
            self.commands[cmd.event].func(cmd)


class Plugin:
    """Simple wrapper class to avoid defining a few common things

    In order for a class to be a plugin it must inherit from this
    class. It defines one method: __init__
    """
    def __init__(self, bot):
        self.bot = bot
        self._sb_meta = PluginMetadata(self)
