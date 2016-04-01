import logging

from seabird.plugin import Plugin

from .isupport import ISupportPlugin, prefix_parse, status_prefix_parse

LOG = logging.getLogger(__name__)


class User:
    def __init__(self, nick):
        self.nick = nick
        self.channels = {}


# Mapping of users to channels and other useful information
class UserTrack(Plugin):
    # See https://gist.github.com/belak/09edcc4f5e51056bf5bc728647659d81 for
    # more info
    def __init__(self, bot):
        super().__init__(bot)

        # Grab the ISUPPORT plugin for PREFIX info
        self.isupport = self.bot.load_plugin(ISupportPlugin)

        # This is just a simple dict which will store all users this bot knows
        # about.
        self.users = {}

        # We use multi-prefix to simplify a few operations. Because it's part
        # of the core IRCv3.1 spec, it should be supported almost everywhere.
        self.bot.cap_req('multi-prefix')

    def get_user(self, nick):
        return self.users.get(nick)

    def add_user(self, nick):
        user = self.get_user(nick)
        if user:
            return user

        LOG.info('Adding user %s', nick)

        user = User(nick)
        self.users[nick] = user
        return user

    def remove_user(self, nick):
        LOG.info('Deleting user %s', nick)

        del self.users[nick]

    def irc_privmsg(self, msg):
        if self.bot.from_channel(msg):
            return

        self.bot.write('JOIN', msg.trailing)

    # Now that the public interface is out of the way, we need to actually get
    # the tracking done.
    def irc_001(self, msg):
        self.add_user(msg.args[0])

    def irc_353(self, msg):
        # RPL_NAMREPLY
        channel = msg.args[2]
        prefix = prefix_parse(self.isupport.supported.get('PREFIX'))

        for nick in msg.args[3].split(' '):
            if not nick:
                continue

            modes, nick = status_prefix_parse(prefix, nick)

            user = self.get_user(nick)
            if not user:
                user = self.add_user(nick)

            user.channels[channel] = modes
            LOG.info('Modes for %s in %s are %s', nick, channel, modes)

    def irc_nick(self, msg):
        oldnick = msg.identity.name
        newnick = msg.args[0]

        if not self.get_user(oldnick):
            raise ValueError('Missing renamed nick {}'.format(oldnick))

        self.users[newnick] = self.get_user(oldnick)
        self.users[newnick].nick = newnick

        del self.users[oldnick]

        LOG.info('Nick renamed %s --> %s', oldnick, newnick)

    def irc_part(self, msg):
        if msg.event == 'PART':
            user = self.get_user(msg.identity.name)
        else:
            user = self.get_user(msg.args[1])

        channel = msg.args[0]
        if not user:
            LOG.warning("Got a part/kick for nonexistent user: %s in %s",
                        msg.identity.name, msg.args[0])
            return
        elif channel not in user.channels:
            LOG.warning("Got a part/kick for user not in a channel: %s in %s",
                        msg.identity.name, msg.args[0])
            return

        user.channels.pop(channel)

        if user.nick == self.bot.current_nick:
            # We left the channel, so remove all unneeded users
            for u_nick, u_user in list(self.users.items()):
                u_user.channels.pop(channel, None)

                # Don't delete ourselves
                if u_user.nick == self.bot.current_nick:
                    continue

                if not u_user.channels:
                    self.remove_user(u_nick)
        elif not user.channels:
            # If they're not in any tracked channels, we need to forget about
            # them.
            self.remove_user(user.nick)

    # Dirty hack because I'm too lazy to re-implement this for kicks
    irc_kick = irc_part

    def irc_mode(self, msg):
        pass

    def irc_quit(self, msg):
        self.remove_user(msg.identity.name)
