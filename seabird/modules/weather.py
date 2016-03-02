import asyncio
from datetime import date

import aiohttp
from sqlalchemy import Column, Float, String

from seabird.plugin import Plugin, CommandMixin

from .db import Base, DatabaseMixin
from .utils import fetch_location, LocationException, Location


FORECAST_URL = "https://api.forecast.io/forecast/{}/{:.4f},{:.4f}"


class WeatherLocation(Base):
    __tablename__ = 'weather_locations'

    nick = Column(String, primary_key=True)
    address = Column(String)
    lat = Column(Float)
    lon = Column(Float)


class WeatherPlugin(Plugin, CommandMixin, DatabaseMixin):
    def __init__(self, bot):
        super().__init__(bot)

        self.key = bot.config['FORECAST_KEY']

    async def fetch_location(self, msg):
        search_loc = msg.trailing.strip()
        loc = None
        if not search_loc:
            with self.db.session() as session:
                db_loc = session.query(WeatherLocation).filter(
                    WeatherLocation.nick == msg.identity.name).one_or_none()

                if not db_loc:
                    raise LocationException('No stored location found.')

                loc = Location(db_loc.address, db_loc.lat, db_loc.lon)

        if loc is None:
            loc = await fetch_location(search_loc)

        # Update the stored location for the given nick
        with self.db.session() as session:
            weather_loc, _ = session.get_or_create(WeatherLocation,
                                                   nick=msg.identity.name)
            weather_loc.address = loc.address
            weather_loc.lat = loc.lat
            weather_loc.lon = loc.lon
            session.add(weather_loc)
            session.flush()

        return loc

    def cmd_forecast(self, msg):
        loop = asyncio.get_event_loop()
        loop.create_task(self.forecast_callback(msg))

    async def forecast_callback(self, msg):
        try:
            loc = await self.fetch_location(msg)
        except LocationException as exc:
            self.bot.mention_reply(msg, exc)
            return

        async with aiohttp.get(FORECAST_URL.format(self.key, loc.lat, loc.lon)) as resp:
            if resp.status != 200:
                self.bot.mention_reply(msg, 'Could not get weather data.')
                return

            data = await resp.json()

            self.bot.mention_reply(msg, '3 day forecast for {}.'.format(loc.address))
            for day in data['daily']['data'][:3]:
                weekday = date.fromtimestamp(day['time']).strftime('%A')
                print(day)

                self.bot.mention_reply(
                    msg,
                    "{}: High {:.2f}, Low {:.2f}, Humidity {:.0f}. {}".format(
                        weekday,
                        day['temperatureMax'],
                        day['temperatureMin'],
                        day['humidity']*100,
                        day['summary'],
                    ),
                )

    def cmd_weather(self, msg):
        loop = asyncio.get_event_loop()
        loop.create_task(self.weather_callback(msg))

    async def weather_callback(self, msg):
        try:
            loc = await self.fetch_location(msg)
        except LocationException as exc:
            self.bot.mention_reply(msg, exc)
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
