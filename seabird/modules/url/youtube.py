import asyncio
from urllib.parse import parse_qs

import aiohttp
from isodate import parse_duration

from ...plugin import Plugin

from . import URLMixin


YOUTUBE_URL = ("https://www.googleapis.com/youtube/v3/videos?"
               "part=contentDetails%2Csnippet&id={}&"
               "fields=items(contentDetails%2Csnippet)&key={}")


class YoutubeURLPlugin(Plugin, URLMixin):
    def url_match(self, msg, url):
        video_id = None
        if url.netloc == 'youtube.com':
            query = parse_qs(url.query)
            video_id = query.get("v")[0]
        elif url.netloc == 'youtu.be':
            video_id = url.path[1:]

        if video_id is None:
            return False

        loop = asyncio.get_event_loop()
        loop.create_task(self.url_callback(msg, video_id))
        return True

    async def url_callback(self, msg, video_id):
        url = YOUTUBE_URL.format(video_id, self.bot.config['YOUTUBE_KEY'])
        async with aiohttp.get(url) as resp:
            data = await resp.json()
            if not data:
                return

            # Pull what we need out of the response
            video = data['items'][0]
            duration = parse_duration(video['contentDetails']['duration'])
            title = video['snippet']['title']

            self.bot.reply(msg, '[YouTube] {} ~ {}'.format(title, duration))
