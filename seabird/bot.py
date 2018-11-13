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
        # If there was no loop, default to grabbing one
        self.loop = loop or asyncio.get_event_loop()
        self.config = config

        self.plugins = []
        self.current_nick = self.config["NICK"]

        # Initialize the underlying protocol
        super().__init__()

    def connection_made(self, transport):
        super().connection_made(transport)

        password = self.config.get("PASS")
        if password is not None:
            self.write("PASS", password)

        self.write("NICK", self.config["NICK"])
        self.write(
            "USER", self.config["USER"], "0.0.0.0", "0.0.0.0", self.config["NAME"]
        )

        # Dispatch this event.
        for plugin in self.plugins:
            plugin.connection_made(self.transport)

    def connection_lost(self, exc):
        super().connection_lost(exc)

        # Dispatch this event
        for plugin in self.plugins:
            plugin.connection_lost(exc)

        self.loop.stop()

    def run(self):
        """Run the bot and wait for it to die"""
        # Make sure to set the current nick
        self.current_nick = self.config["NICK"]

        plugin_classes = self.config.get("PLUGIN_CLASSES")
        plugin_modules = self.config.get("PLUGIN_MODULES")
        if plugin_classes is None and plugin_modules is None:
            plugin_modules = []
            for _, name, _ in walk_packages(modules.__path__, "seabird.modules."):
                plugin_modules.append(name)

        # These are modules which contain multiple plugins. All
        # plugins which are found in these modules will be loaded.
        if plugin_modules is not None:
            for module in plugin_modules:
                LOG.info("Loaded module %s", module)

                mod = import_module(module)

                for name, obj in inspect.getmembers(mod):
                    # This is a simple check to filter out any classes which
                    # aren't from the current plugin module (such as imports)
                    if not inspect.isclass(obj) or obj.__module__ != module:
                        continue

                    # We want to skip any class which is set to disabled,
                    # because they need to be explicitly loaded in
                    # PLUGIN_CLASSES.
                    if getattr(obj, "__disabled__", False):
                        continue

                    # We attempt to load all classes, but ignore the
                    # failures
                    try:
                        self.load_plugin(obj)
                    except TypeError:
                        continue

        # These are all plugins which are explicitly loaded
        if plugin_classes is not None:
            for class_name in self.config.get("PLUGIN_CLASSES", {}):
                self.load_plugin(class_name)

        # Create an SSL context if we asked for one
        ssl_ctx = None
        if self.config["SSL"]:
            ssl_ctx = ssl.create_default_context()
            if not self.config.get("SSL_VERIFY", True):
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

        connector = self.loop.create_connection(
            lambda: self,
            host=self.config["HOST"],
            port=self.config["PORT"],
            ssl=ssl_ctx,
        )

        # Run until complete here will only run until the we are connected,
        # not until the connection is finished.
        self.loop.run_until_complete(connector)

        # In this case, forever means until it's stopped. Specifically in
        # connection_lost.
        self.loop.run_forever()

    def dispatch(self, msg):
        # Ensure current_nick is up to date
        if msg.event == "001":
            self.current_nick = msg.args[0]
        elif msg.event == "NICK" and msg.identity.name == self.current_nick:
            self.current_nick = msg.args[0]
        elif msg.event == "437" or msg.event == "433":
            self.current_nick += "_"
            self.write("NICK", self.current_nick)

        # If we just connected, send all lines
        if msg.event == "001":
            for line in self.config.get("CMDS", []):
                self.write_line(line)

        # Ping pong
        if msg.event == "PING":
            self.write("PONG", *msg.args)

        # Attach the current nick to the message for callbacks
        msg.current_nick = self.current_nick

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
            module, _, name = obj.rpartition(".")
            module = import_module(module)
            plugin_class = getattr(module, name)

        if Plugin not in inspect.getmro(plugin_class):
            raise TypeError("Class {} is not a valid Plugin".format(obj))

        # If it's already loaded, we should just return the already loaded
        # instance.
        for plugin in self.plugins:
            if isinstance(plugin, plugin_class):
                return plugin

        # Initialize the plugin
        plugin = plugin_class(self)

        # Add the plugin to the list
        self.plugins.append(plugin)

        LOG.info("Loaded plugin %s", plugin_class)

        return plugin

    # IRC helpers go here

    def mention_reply(self, event, msg):
        """Reply to and mention the user in the given event"""
        # If the event came from a channel, prepend the nick it came from
        if event.from_channel:
            msg = "{}: {}".format(event.identity.name, msg)

        self.reply(event, msg)

    def reply(self, event, msg):
        """Convenience function which replies to a message"""
        if not event.args or not event.args[0]:
            raise ValueError("Invalid IRC event")

        if event.from_channel:
            self.write("PRIVMSG", event.args[0], msg)
        else:
            self.write("PRIVMSG", event.identity.name, msg)

    def reply_to_user(self, event, msg):
        """Convenience function which replies to a user via PRIVMSG"""
        if not event.args or not event.args[0]:
            raise ValueError("Invalid IRC event")

        self.write("PRIVMSG", event.identity.name, msg)
