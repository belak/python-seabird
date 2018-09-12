import asyncio

import aiohttp

from seabird.plugin import Plugin, CommandMixin


METAR_URL = "http://tgftp.nws.noaa.gov/data/observations/metar/stations/{}.TXT"
TAF_URL = "http://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{}.TXT"


class NOAAPlugin(Plugin, CommandMixin):
    def cmd_taf(self, msg):
        """<station>

        Returns the TAF report given an airport code
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.noaa_callback(TAF_URL, msg))

    def cmd_metar(self, msg):
        """<station>

        Returns the METAR report given an airport code
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.noaa_callback(METAR_URL, msg))

    async def noaa_callback(self, url, msg):
        loc = msg.trailing.upper()
        if not loc.isalnum():
            self.bot.mention_reply(msg, "Not a valid airport code")
            return

        async with aiohttp.ClientSession() as session, session.get(
            url.format(loc)
        ) as resp:
            if resp.status != 200:
                self.bot.mention_reply(msg, "Could not find data for station")
                return

            data = await resp.text()
            for line in data.splitlines()[1:]:
                self.bot.mention_reply(msg, line.strip())
