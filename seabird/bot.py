import asyncio
from importlib import import_module
import inspect
import logging
from pkgutil import walk_packages
import ssl

from .plugin import Plugin
from .irc import Protocol
from . import modules

LOG = logging.getLogger(__name__)


class Bot(Protocol):
    def __init__(self, config, loop=None):
        self.config = config

        # Initialize the underlying connection
        super().__init__(self.config['NICK'],
                         self.config['USER'],
                         self.config['NAME'],
                         self.config['PASS'])

        self.plugins = []

        # If there was no loop, default to grabbing one
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop

    def handshake(self):
        # NOTE: This is actually the dispatch for connection_made, but because
        # we need to do the processing for the IRCProtocol before this is
        # called, we override handshake.

        # Dispatch this event.
        for plugin in self.plugins:
            plugin.connection_made(self.transport)

        super().handshake()

    def connection_lost(self, exc):
        super().connection_lost(exc)

        # Dispatch this event
        for plugin in self.plugins:
            plugin.connection_lost(exc)

        # If the config tells us to restart, we restart. Otherwise we
        # completely bail so this isn't silently lost.
        if self.config.get('RECONNECT_ON_FAILURE', True):
            reconnect_delay = self.config.get('RECONNECT_DELAY', 5)

            if reconnect_delay > 0:
                # This will allow the loop to run until we want to reconnect.
                self.loop.run_until_complete(asyncio.sleep(reconnect_delay))

            bot = Bot(self.config, loop=self.loop)
            bot.run()
        else:
            self.loop.stop()

    def dispatch(self, msg):
        if msg.event == '001':
            for line in self.config.get('CMDS', []):
                self.write_line(line)

        # Dispatch all events
        for plugin in self.plugins:
            plugin.dispatch_event(msg)

    def load_plugin(self, obj):
        """Load and return a given plugin

        This can take either a class or a string as the one argument.
        """
        if inspect.isclass(obj):
            plugin_class = obj
        else:
            module, _, name = obj.rpartition('.')
            module = import_module(module)
            plugin_class = getattr(module, name)

        if Plugin not in inspect.getmro(plugin_class):
            raise TypeError('Class {} is not a valid Plugin'.format(obj))

        # If it's already loaded, we should just return the already loaded
        # instance.
        for plugin in self.plugins:
            if isinstance(plugin, plugin_class):
                return plugin

        # Initialize the plugin
        plugin = plugin_class(self)

        # Add the plugin to the list
        self.plugins.append(plugin)

        LOG.info('Loaded plugin %s', plugin_class)

        return plugin

    def run(self):
        """Run the bot and wait for it to die"""
        # Make sure to set the current nick
        self.current_nick = self.config['NICK']

        plugin_classes = self.config.get('PLUGIN_CLASSES')
        plugin_modules = self.config.get('PLUGIN_MODULES')
        if plugin_classes is None and plugin_modules is None:
            plugin_modules = []
            for _, name, _ in walk_packages(modules.__path__, 'seabird.modules.'):  # noqa
                plugin_modules.append(name)

        # These are modules which contain multiple plugins. All
        # plugins which are found in these modules will be loaded.
        if plugin_modules is not None:
            for module in plugin_modules:
                LOG.info('Loaded module %s', module)

                mod = import_module(module)

                for name, obj in inspect.getmembers(mod):
                    # This is a simple check to filter out any classes which
                    # aren't from the current plugin module (such as imports)
                    if not inspect.isclass(obj) or obj.__module__ != module:
                        continue

                    # We attempt to load all classes, but ignore the
                    # failures
                    try:
                        self.load_plugin(obj)
                    except TypeError:
                        continue

        # These are all plugins which are explicitly loaded
        if plugin_classes is not None:
            for class_name in self.config.get('PLUGIN_CLASSES', {}):
                self.load_plugin(class_name)

        # Create an SSL context if we asked for one
        ssl_ctx = None
        if self.config['SSL']:
            ssl_ctx = ssl.create_default_context()
            if not self.config.get('SSL_VERIFY', True):
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

        connector = self.loop.create_connection(lambda: self,
                                                host=self.config['HOST'],
                                                port=self.config['PORT'],
                                                ssl=ssl_ctx)

        # Run until complete here will only run until the we are connected, not
        # until the connection is finished.
        self.loop.run_until_complete(connector)

    def run_forever(self):
        """Run the bot and wait for it to die"""
        self.run()
        self.loop.run_forever()

    # IRC helpers go here

    def from_channel(self, event):
        # TODO: Figure out what to do about this. This will only really be
        # valid for PRIVMSG messages and related other messages.
        if len(event.args) < 2:
            return False

        # If the location is the current nick, we know it's a private message.
        # This saves on mucking about with ISupport and other such nonsense and
        # lets us keep this as simple as possible.
        if event.args[0] == self.current_nick:
            return False

        return True

    def mention_reply(self, event, msg):
        """Reply to and mention the user in the given event"""
        # If the event came from a channel, prepend the nick it came from
        if self.from_channel(event):
            msg = '{}: {}'.format(event.identity.name, msg)

        self.reply(event, msg)

    def reply(self, event, msg):
        """Convenience function which replies to a message"""
        if len(event.args) < 1 or len(event.args[0]) < 1:
            raise ValueError('Invalid IRC event')

        if self.from_channel(event):
            self.write('PRIVMSG', event.args[0], msg)
        else:
            self.write('PRIVMSG', event.identity.name, msg)
