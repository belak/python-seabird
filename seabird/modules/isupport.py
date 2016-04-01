# Code from this plugin is based off PyIRC (https://code.foxkit.us/IRC/PyIRC/)
# originally licensed under the WTFPL v2 and Copyright © 2013-2015 Elizabeth
# Myers and Andrew Wilcox.
#
# It has been modified to work with seabird rather than PyIRC and is included
# in seabird under the seabird license terms available in the root of the repo.

from copy import deepcopy
from collections import namedtuple
import logging
import re

from seabird.plugin import Plugin

LOG = logging.getLogger(__name__)
PREFIX_REGEX = re.compile(r"\(([A-Za-z0-9]+)\)(.+)")

ParsedPrefix = namedtuple("ParsedPrefix", "mode_to_prefix prefix_to_mode")


def prefix_parse(prefix):
    match = PREFIX_REGEX.match(prefix)
    if not match:
        raise ValueError("Prefix does not match expected format")

    modes, values = match.groups()
    if len(modes) != len(values):
        raise ValueError("Unbalanced modes and prefixes")

    ret = ParsedPrefix({}, {})
    for k, v in zip(modes, values):
        ret.mode_to_prefix[k] = v
        ret.prefix_to_mode[v] = k

    return ret


def status_prefix_parse(prefix, string):
    prefix = prefix.prefix_to_mode

    modes = set()
    while string[0] in prefix:
        prefix_char, string = string[0], string[1:]
        modes.add(prefix[prefix_char])

    return (modes, string)


class ISupportPlugin(Plugin):
    defaults = {
        "PREFIX": ['o', 'v', '@', '+'],
        "CHANTYPES": '#&!+',
        "NICKLEN": "8",
        "CASEMAPPING": "RFC1459",
        "CHANMODES": ['b', 'k', 'l', 'imnstp'],
    }

    def __init__(self, bot):
        super().__init__(bot)

        # Copy over the initial defaults
        self.supported = deepcopy(self.defaults)

    def irc_005(self, msg):
        # This is based off of PyIRC.extensions.isupport.ISupport.isupport and
        # PyIRC.auxparse.isupport_parse.
        if not msg.args[-1].endswith('server'):
            raise ValueError('Really old IRC server. '
                             'It may be fine, but things might break.')

        # Note that we skip the first and last args because the first is our
        # nick and the last should be "are supported by this server"
        supported = {}
        for param in msg.args[1:-1]:
            # Split into key, value pairs
            key, _, value = param.partition('=')

            # eg, EXCEPTS
            if not value:
                LOG.info('ISUPPORT [k]: %s', key)
                supported[key] = True
                continue

            # Split into CSVs. For each CSV, parse into pairs of val, data.
            ret_dict = {}
            ret_list = []
            for inner_val in value.split(','):
                # eg, MAXLIST=ACCEPT:,TEST:5
                val, sep, data = inner_val.rpartition(':')
                if sep:
                    if not data:
                        data = None

                    ret_dict[val] = data
                else:
                    ret_list.append(data)

            # No use in having a list if there's only one item.
            if len(ret_list) == 1:
                ret_list = ret_list[0]

            # TODO: This *might* be possible but it should be extremely
            # rare... and there isn't really a proper way to handle it so we
            # just ignore it.
            if ret_list and ret_dict:
                raise ValueError('ISupport with both list and dict value')

            # If the dict and list are empty, we just enable the value
            if ret_dict:
                supported[key] = ret_dict
            elif ret_list:
                supported[key] = ret_list
            else:
                supported[key] = True

            LOG.info('ISUPPORT [k:v] %s:%s', key, supported[key])

        self.supported.update(supported)
