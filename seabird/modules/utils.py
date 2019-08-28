from collections import namedtuple

import aiohttp


GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


Location = namedtuple("Location", ["address", "lat", "lon"])


class LocationException(Exception):
    pass


async def fetch_location(address):
    async with aiohttp.ClientSession() as session, session.get(
        GEOCODE_URL, params={"address": address, "sensor": False}
    ) as resp:
        if resp.status != 200:
            raise LocationException("Failed to lookup address")

        data = await resp.json()
        res = data["results"]
        if not res:
            raise LocationException("No location results found")

        if len(res) > 1:
            raise LocationException("More than 1 location result")

        loc = res[0]["geometry"]["location"]
        return Location(res[0]["formatted_address"], loc["lat"], loc["lng"])


async def fetch_json(*args, **kwargs):
    async with aiohttp.ClientSession() as session, session.get(*args, **kwargs) as resp:
        data = await resp.json()
        if data:
            return data

    return None
