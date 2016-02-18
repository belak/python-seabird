import asyncio
import re

import aiohttp

from ...plugin import Plugin

from . import URLMixin


class XKCDUrlPlugin(Plugin, URLMixin):
    url_regex = re.compile(r'https?://xkcd\.com(/\d+)?/?$')

    def url_match(self, msg, url):
        match = XKCDUrlPlugin.url_regex.match(url)
        if match is None:
            return False

        loop = asyncio.get_event_loop()
        loop.create_task(self.url_callback(msg, url+'/info.0.json'))

        return True

    async def url_callback(self, msg, url):
        async with aiohttp.get(url) as resp:
            data = await resp.json()
            if not data:
                return

            self.bot.reply(msg, '[XKCD] {}: {}'.format(
                data['title'], data['alt']))
