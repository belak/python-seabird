import asyncio
import re

import aiohttp

from ...plugin import Plugin

from . import URLPlugin, URLMixin


class XKCDURLPlugin(Plugin, URLMixin):
    url_regex = re.compile(r'(/\d+)?/?$')

    def __init__(self, bot):
        super().__init__(bot)

        self.bot.load_plugin(URLPlugin)

    def url_match(self, msg, url):
        if url.netloc != 'xkcd.com':
            return False

        match = XKCDURLPlugin.url_regex.match(url.path)
        if match is None:
            return False

        url = url._replace(path=url.path+'/info.0.json')

        loop = asyncio.get_event_loop()
        loop.create_task(self.url_callback(msg, url.geturl()))

        return True

    async def url_callback(self, msg, url):
        async with aiohttp.get(url) as resp:
            data = await resp.json()
            if not data:
                return

            self.bot.reply(msg, '[XKCD] {}: {}'.format(
                data['title'], data['alt']))
