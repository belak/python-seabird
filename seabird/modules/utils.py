from collections import namedtuple

import aiohttp


GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


Location = namedtuple('Location', ['address', 'lat', 'lon'])


class LocationException(Exception):
    pass


async def fetch_location(address):
    async with aiohttp.get(GEOCODE_URL, params={
        'address': address, "sensor": False,
    }) as resp:
        if resp.status != 200:
            raise LocationException('Failed to lookup address')

        data = await resp.json()
        res = data['results']
        if len(res) == 0:
            raise LocationException('No location results found')
        elif len(res) == 0:
            raise LocationException('More than 1 location result')

        loc = res[0]['geometry']['location']
        return Location(res[0]['formatted_address'], loc['lat'], loc['lng'])
