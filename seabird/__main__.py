from asyncio import get_event_loop

from .config import Config
from .bot import Bot

def main():
    loop = get_event_loop()

    conf = Config()
    conf.from_module('config')

    bot = Bot(conf, loop=loop)
    bot.run()

    loop.run_forever()
    loop.close()

main()
