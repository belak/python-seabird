import asyncio
import re
from urllib.parse import urlparse

import aiohttp
import lxml.html

from seabird.plugin import Plugin


class URLMixin:
    """Simple marker class to mark a plugin as a url plugin

    A URL plugin requires only one thing:
    - A method named url_match which takes a msg and url as an argument and
      returns True if the url matches this plugin.

    Note that callback functions are not required to be coroutines in case they
    need to access data from other plugins, but most should have a background
    task as almost every one will need to do some form of background processing
    or data transfer.
    """
    def url_match(self, msg, url):
        raise NotImplementedError


class URLPlugin(Plugin):
    url_regex = re.compile(r'https?://[^ ]+')

    def irc_privmsg(self, msg):
        for match in URLPlugin.url_regex.finditer(msg.trailing):
            url = match.group(0)
            parsed_url = urlparse(url)

            matching_plugin = False
            for plugin in self.bot.plugins:
                if (isinstance(plugin, URLMixin) and
                        plugin.url_match(msg, parsed_url)):
                    matching_plugin = True

            # As a fallback, use our own internal URL handler
            if not matching_plugin:
                loop = asyncio.get_event_loop()
                loop.create_task(self.url_callback(msg, url))

    async def url_callback(self, msg, url):
        async with aiohttp.get(url) as resp:
            # Read up to 1m
            data = await resp.content.read(1024*1024)
            if not data:
                return

            # lxml has an implementation of xpath, so we use that to search for
            # the title tag.
            tree = lxml.html.fromstring(data)
            title = tree.find(".//title")
            if title is None or title.text is None:
                return

            text = title.text.translate({
                '\t': None,
                '\n': None,
                '\v': None,
            }).strip()

            if not text:
                return

            self.bot.reply(msg, 'Title: {}'.format(text))
