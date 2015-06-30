import asyncio
from importlib import import_module
import inspect
import ssl
from types import ModuleType

from .config import BotConfig
from .plugin import Plugin
from .irc import Protocol, Message


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
        cmd = None
        if (msg.event == "PRIVMSG" and
                msg.trailing.startswith(self.config['PREFIX'])):
            cmd = Message(msg.line)

            # Remove the last arg so we can recreate it. Note that we
            # skip the prefix.
            split = cmd.trailing[len(self.config['PREFIX']):].split(' ', 1)
            cmd.event = split[0]

            # Replace trailing
            cmd.trailing = ''
            if len(split) > 1:
                cmd.trailing = split[1]

            # Replace the last arg
            cmd.args.pop()
            cmd.args.append(cmd.trailing)

        for plugin in self.plugins:
            plugin._sb_meta.dispatch_event(self, msg)

            # Dispatch the command if we have it
            if cmd is not None:
                plugin._sb_meta.dispatch_command(self, cmd)

    def _load_plugin(self, module, name):
        # NOTE: This can take either a module or a string
        if type(module) != ModuleType:
            module = import_module(module)

        plugin_class = getattr(module, name)

        if Plugin not in inspect.getmro(plugin_class):
            raise TypeError('Class %s.%s is not a valid Plugin' %
                            (module.__name__, name))

        plugin = plugin_class(self)

        # Now that we have a plugin, we can generate the metadata
        # for it
        plugin.generate_metadata()

        self.plugins.append(plugin)

    def run(self):
        """Run the bot and wait for it to die"""
        # These are modules which contain multiple plugins. All
        # plugins which are found in these modules will be loaded.
        for module in self.config.get('PLUGIN_MODULES', []):
            print('Loading module %s' % module)

            mod = import_module(module)

            # This is a simple function which will filter out any
            # classes which aren't from the current plugin module
            # (such as imports)
            def valid_mod(member):
                return inspect.isclass(member) and member.__module__ == module

            for name, obj in inspect.getmembers(mod, valid_mod):
                # We attempt to load all classes, but ignore the
                # failures
                try:
                    self._load_plugin(mod, name)
                except TypeError:
                    continue

                print('Loaded plugin %s.%s' % (module, name))

        # These are all plugins which are explicitly loaded
        for module, name in self.config.get('PLUGIN_CLASSES', {}):
            self._load_plugin(module, name)

        # Create an SSL context if we asked for one
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
        """Simple proxy to the irc.Protocol.write method"""
        return self.client.write(*args, **kwargs)

    def mention_reply(self, event, msg):
        """Reply to and mention the user in the given event"""
        # If the event came from a channel, prepend the nick it came from
        if event.from_channel():
            msg = '%s: %s' % (event.identity.name, msg)

        self.reply(event, msg)

    def reply(self, event, msg):
        """Convenience function which replies to a message"""
        if len(event.args) < 1 or len(event.args[0]) < 1:
            raise ValueError('Invalid IRC event')

        if event.from_channel():
            self.write(('PRIVMSG', event.args[0]), trailing=msg)
        else:
            self.write(('PRIVMSG', event.identity.name), trailing=msg)
