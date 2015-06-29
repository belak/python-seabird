import asyncio
from importlib import import_module
import ssl

from .config import BotConfig
from .irc import Protocol


# TODO: Exception handling
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

                self.commands[command] = func

            for event in func_meta.events:
                if event not in self.events:
                    self.events[event] = []

                self.events[event].append(func)

    def dispatch_event(self, bot, event):
        for func in self.events.get(event.event, []):
            func(bot, event)

    def dispatch_command(self, cmd):
        raise NotImplementedError


class Bot:
    def __init__(self, loop=None):
        self.config = BotConfig()
        self.client = Protocol(self.dispatch, self.config)
        self.plugins = []

        # If there was no loop, default to grabbing one
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop

    def dispatch(self, msg):
        for plugin in self.plugins:
            plugin._sb_meta.dispatch_event(self, msg)

        # TODO: Dispatch command

    def run(self):
        for module, name in self.config['PLUGIN_CLASSES']:
            # TODO: This can fail if parent modules are not imported
            plugin_module = import_module(module)
            plugin_class = getattr(plugin_module, name)
            plugin = plugin_class(self)

            # Now that we have a plugin, we can generate the metadata
            # for it
            plugin._sb_meta = PluginMetadata(plugin)

            self.plugins.append(plugin)

        ssl_ctx = None
        if self.config['SSL']:
            ssl_ctx = ssl.create_default_context()
            if not self.config['SSL_VERIFY']:
                ssl_ctx.verify_mode = ssl.CERT_NONE

        connector = self.loop.create_connection(lambda: self.client,
                                                host=self.config['HOST'],
                                                port=self.config['PORT'],
                                                ssl=ssl_ctx)

        transport, protocol = self.loop.run_until_complete(connector)
        self.loop.run_forever()

    # IRC helpers go here

    def write(self, *args, **kwargs):
        """Simple proxy to the irc.Protocol.write"""
        return self.client.write(*args, **kwargs)
