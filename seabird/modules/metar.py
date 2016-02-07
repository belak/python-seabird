import asyncio

import aiohttp

from seabird.decorators import command
from seabird.plugin import Plugin


METAR_URL = 'http://weather.noaa.gov/pub/data/observations/metar/stations/%s.TXT'


class MetarPlugin(Plugin):
    @command
    def metar(self, msg):
        """<station>

        Returns the METAR report given an airport code
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.metar_callback(msg))

    async def metar_callback(self, msg):
        loc = msg.trailing.upper()
        if not loc.isalnum():
            self.bot.mention_reply(msg, 'Not a valid airport code')
            return

        async with aiohttp.get(METAR_URL % loc) as resp:
            if resp.status != 200:
                self.bot.mention_reply(msg, 'Could not find data for station')
                return

            found = False
            data = await resp.text()
            for line in data.splitlines():
                if line.startswith(loc):
                    found = True
                    self.bot.mention_reply(msg, line)

            if not found:
                self.bot.mention_reply(msg, 'No results')
