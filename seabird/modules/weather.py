import asyncio

import aiohttp
from sqlalchemy import Column, Float, String

from seabird.plugin import Plugin, CommandMixin

from .db import Base, DatabasePlugin
from .utils import fetch_location, LocationException


FORECAST_URL = "https://api.forecast.io/forecast/{}/{:.4f},{:.4f}"

class WeatherLocation(Base):
    __tablename__ = 'weather_locations'

    nick = Column(String, primary_key=True)
    address = Column(String)
    lat = Column(Float)
    lon = Column(Float)

class WeatherPlugin(Plugin, CommandMixin):
    def __init__(self, bot):
        super().__init__(bot)

        self.key = bot.config['FORECAST_KEY']

        self.db = self.bot.load_plugin(DatabasePlugin)

    def cmd_forecast(self, msg):
        loc = {}

        loop = asyncio.get_event_loop()
        loop.create_task(self.forecast_callback(msg, loc))

    async def forecast_callback(self, msg, loc):
        pass

    def cmd_weather(self, msg):
        loop = asyncio.get_event_loop()
        loop.create_task(self.weather_callback(msg))

    async def weather_callback(self, msg):
        try:
            loc = await fetch_location(msg.trailing)
        except LocationException as e:
            self.bot.mention_reply(msg, e)
            return

        async with aiohttp.get(FORECAST_URL.format(self.key, loc.lat, loc.lon)) as resp:
            if resp.status != 200:
                self.bot.mention_reply(msg, 'Could not get weather data.')
                return

            data = await resp.json()

            today = data['daily']['data'][0]
            currently = data['currently']

            self.bot.mention_reply(
                msg,
                "{}. Currently {:.1f}. High {:.2f}, Low {:.2f}, "
                "Humidity {:.0f}. {}.".format(
                    loc.address,
                    currently['temperature'],
                    today['temperatureMax'],
                    today['temperatureMin'],
                    currently['humidity']*100,
                    currently['summary'],
                ),
            )
