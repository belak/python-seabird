import asyncio


def _decode_tag(data):
    # https://github.com/ircv3/ircv3-specifications/blob/master/core/message-tags-3.2.md#escaping-values
    mapping = [
        (';', '\\:'),
        (' ', '\\s'),
        ('\\', '\\\\'),
        ('\r', '\\r'),
        ('\n', '\\n')
    ]
    for k, v in mapping:
        data = data.replace(k, v)

    return data


# TODO: Debug logging
# TODO: Documentation
# TODO: Parse hostmask
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
            tags = line[1:].split(' ', 1).split(';')

            # Store all the tags
            for tag, val in tags:
                tag = tag.split('=', 1)
                if len(tag) > 1:
                    self.tags[tag[0]] = _decode_tag(tag[1])
                else:
                    self.tags[tag[0]] = None

        self.hostmask = None
        if line.startswith(':'):
            # This is similar to the above line. We skip the first
            # char because we don't care about it, then split on the
            # first space.
            self.hostmask, line = line[1:].split(' ', 1)

        self.trailing = None

        # Splitting on the first space followed by a colon is the
        # start of the trailing argument.
        args = line.split(' :', 1)
        if len(args) > 1:
            self.trailing = args[1]

        # Split the args and grab the first one as the event
        self.args = args[0].split(' ')
        self.event = self.args[0]
        self.args = self.args[1:]

        # If trailing isn't none, we add it back to the args
        if self.trailing is not None:
            self.args.append(self.trailing)


class Protocol(asyncio.Protocol):
    def __init__(self, dispatch, config):
        self.dispatch = dispatch
        self.config = config

    def connection_made(self, transport):
        self.transport = transport
        self.buf = ''

        if 'PASS' in self.config:
            self.write(('PASS', self.config['PASS']))

        self.write(('NICK',), self.config['NICK'])
        self.write(('USER', self.config['USER'], '0.0.0.0', '0.0.0.0'),
                   trailing=self.config['NAME'])

    def data_received(self, data):
        self.buf += data.decode()

        while '\n' in self.buf:
            # Find the first \n, and split on that.
            line, self.buf = self.buf.split('\n', 1)

            # Because we're only looking for \n in the sake of
            # compatibility, we strip any trailing \r characters.
            line.rstrip('\r')

            # We got a line!
            print('<< %s' % line)

            msg = Message(line)

            # The only thing important enough to be in the protocol
            # itself is sending of pongs.
            if msg.event == "PING":
                self.write(("PONG",), trailing=msg.args[-1])

            # Send the message to whoever's using this
            self.dispatch(Message(line))

    def write(self, args, trailing=None):
        # Create the args portion of the line
        line = ' '.join(args)

        # If there's trailing, write it out
        if trailing is not None:
            line += ' :' + trailing

        # Make sure the line is only 510 characters before adding the
        # \r\n
        line = line[:510]

        print('>> %s' % line)

        # Add in the \r\n and send it
        line += '\r\n'
        self.transport.write(line.encode('utf-8'))

    def connection_lost(self, e):
        # TODO: Handle failures better
        pass
