import asyncio
import re

import aiohttp
import lxml.html

from seabird.plugin import Plugin


class URLPlugin(Plugin):
    url_regex = re.compile(r'https?://[^ ]+')

    def irc_privmsg(self, msg):
        for match in URLPlugin.url_regex.finditer(msg.trailing):
            url = match.group(0)

            # As a fallback, use our own internal URL handler
            if True:
                loop = asyncio.get_event_loop()
                loop.create_task(self.url_callback(msg, url))

    async def url_callback(self, msg, url):
        async with aiohttp.get(url) as resp:
            # Read up to 1m
            data = await resp.content.read(1024*1024)
            if not data:
                return

            tree = lxml.html.fromstring(data)
            title = tree.find(".//title")
            if title is None:
                return

            self.bot.reply(msg, 'Title: {}'.format(title.text))
