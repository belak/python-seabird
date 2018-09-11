from .irc import Message


class CommandMixin:
    def irc_privmsg(self, event):
        if event.event != 'PRIVMSG':
            return

        if not event.trailing.startswith(self.bot.config['PREFIX']):
            return

        # Create a new message
        cmd = Message(event.line, current_nick=event.current_nick)
        split = cmd.trailing[len(self.bot.config['PREFIX']):].split(' ', 1)
        cmd.event = split[0]

        # Replace the last arg with everything after the command being called.
        cmd.args.pop()
        if len(split) > 1:
            cmd.args.append(split[1])
        else:
            cmd.args.append('')

        # Send it off!
        self.dispatch_command(cmd)

    def dispatch_command(self, cmd):
        callback = getattr(self, "cmd_{}".format(cmd.event.lower()), None)
        if not callback:
            return

        callback(cmd)


class Plugin:
    """Simple wrapper class to avoid defining a few common things

    In order for a class to be a plugin it must inherit from this class. It
    defines __init__ and dispatch_event.

    This class needs to call super with no arguments so it can properly
    instantiate 'object'. Because of this, any mixins which need to rely on
    having a reference to the bot object need to either use self.bot or be
    before Plugin in the MRO.
    """
    def __init__(self, bot):
        self.bot = bot

        super().__init__()

    def connection_made(self, transport):
        """Stub method for protocol level connection_made"""
        pass

    def connection_lost(self, exc):
        """Stub method for protocol level connection_lost"""
        pass

    def dispatch_event(self, event):
        """Attempt to dispatch an event

        This works in a manner similar to the twisted.words irc module. If a
        callback exists, we use it.
        """
        callback = getattr(self, "irc_{}".format(event.event.lower()), None)
        if not callback:
            return

        callback(event)
