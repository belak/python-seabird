import asyncio
import logging

LOG = logging.getLogger(__name__)


def _decode_tag(data):
    # https://github.com/ircv3/ircv3-specifications/blob/master/core/message-tags-3.2.md#escaping-values
    mapping = [
        (';', '\\:'),
        (' ', '\\s'),
        ('\\', '\\\\'),
        ('\r', '\\r'),
        ('\n', '\\n')
    ]
    for key, val in mapping:
        data = data.replace(key, val)

    return data


class Identity:
    # name!user@host
    def __init__(self, raw):
        self.raw = raw
        self.user = None
        self.host = None
        self.name = None

        split = raw.split('@', 1)
        if len(split) != 2:
            return

        self.user, self.host = split

        split = self.user.split('!', 1)
        if len(split) != 2:
            return

        self.name, self.user = split


class Message:
    def __init__(self, line):
        self.line = line

        # IRCv3 message tags
        self.tags = {}
        if line.startswith('@'):
            # This looks much worse than it actually is. We skip the
            # first character (as it's an @) and we grab the first
            # section (up to the first space) and because we only have
            # one, we split on ; to get the tags in a list.
            tags = line[1:].split(' ', 1)[0].split(';')

            # Store all the tags
            for tag in tags:
                tag = tag.split('=', 1)
                if len(tag) > 1:
                    self.tags[tag[0]] = _decode_tag(tag[1])
                else:
                    self.tags[tag[0]] = None

        self.hostmask = None
        self.identity = None
        if line.startswith(':'):
            # This is similar to the above line. We skip the first
            # char because we don't care about it, then split on the
            # first space.
            self.hostmask, line = line[1:].split(' ', 1)
            self.identity = Identity(self.hostmask)

        # Splitting on the first space followed by a colon is the
        # start of the trailing argument.
        trailing = None
        args = line.split(' :', 1)
        if len(args) > 1:
            trailing = args[1]

        # Split the args and grab the first one as the event
        self.args = args[0].split(' ')
        self.event = self.args[0]
        self.args = self.args[1:]

        # If trailing isn't none, we add it back to the args
        if trailing is not None:
            self.args.append(trailing)

    @property
    def trailing(self):
        return self.args[-1]


class Protocol(asyncio.Protocol):
    def __init__(self, nick, user, name, password=None):
        self.nick = nick
        self.user = user
        self.name = name
        self.password = password

        self.current_nick = nick
        self.caps_requested = set()
        self.caps_available = set()
        self.handshake_done = False

        # These are actually initialized in connection_made, but we put it here
        # so pylint won't complain.
        self.transport = None
        self.buf = ''

    def connection_made(self, transport):
        self.transport = transport
        self.buf = ''
        self.handshake_done = False

        # NOTE: handshake is provided so a method can hook into connection_made
        # after the variables have been cleared, but before we send data to the
        # server.
        self.handshake()

    def handshake(self):
        if self.password is not None:
            self.write('PASS', self.password)

        if len(self.caps_requested) != 0:
            # We request all caps separately to keep things simple.
            for cap in self.caps_requested:
                self.write('CAP', 'REQ', cap)
        else:
            self.finalize_handshake()

    def finalize_handshake(self):
        self.write('CAP', 'END')
        self.write('NICK', self.nick)
        self.write('USER', self.user, '0.0.0.0', '0.0.0.0', self.name)
        self.handshake_done = True

    def data_received(self, data):
        self.buf += data.decode()

        while '\n' in self.buf:
            # Find the first \n, and split on that.
            line, self.buf = self.buf.split('\n', 1)

            # Because we're only looking for \n in the sake of
            # compatibility, we strip any trailing \r characters.
            line = line.rstrip('\r')

            # We got a line!
            LOG.debug('<-- %s', line)

            msg = Message(line)

            # There are very few things actually important enough to be
            # here. CAP handling, PING/PONG, and current_nick are among those.
            if msg.event == '001':
                self.current_nick = msg.args[0]
            elif (msg.event == 'NICK' and
                  msg.identity.name == self.current_nick):
                self.current_nick = msg.args[0]
            elif msg.event == "437" or msg.event == "433":
                self.current_nick += '_'
                self.write('NICK', self.current_nick)
            elif msg.event == 'CAP':
                if msg.args[1] == 'ACK':
                    for cap in msg.args[2:]:
                        self.caps_available.add(cap)

                    enough_caps = len(self.caps_available) <= len(self.caps_requested)
                    if not self.handshake_done and enough_caps:
                        self.finalize_handshake()
                elif msg.args[0] == 'NAK':
                    raise RuntimeError('CAP(s)) {} not supported by server'.format(msg.args[1:]))
            elif msg.event == "PING":
                self.write("PONG", *msg.args)

            # Send the message to whoever's using this
            self.dispatch(msg)

    def cap_req(self, cap):
        if self.handshake_done:
            # TODO: This should still make the request
            raise RuntimeError('CAP requested after handshake')

        self.caps_requested.add(cap)

    def write(self, *args):
        # If the final argument contains a space, it needs to be encoded as a
        # trailing argument.
        trailing = None
        if ' ' in args[-1]:
            trailing = args[-1]
            args = args[:-1]

        # Create the args portion of the line
        line = ' '.join(args)

        # Append trailing if we have any
        if trailing is not None:
            line += ' :' + trailing

        # Make sure the line is only 510 characters before adding the
        # \r\n
        line = line[:510]

        self.write_line(line)

    def write_line(self, line):
        LOG.debug('--> %s', line)

        # Add in the \r\n and send it
        line += '\r\n'
        self.transport.write(line.encode('utf-8'))

    def dispatch(self, msg):
        raise NotImplementedError

    def connection_lost(self, e):
        # TODO: Handle failures better
        pass
