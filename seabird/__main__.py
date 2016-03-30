from asyncio import get_event_loop
import logging

from colorlog import ColoredFormatter

from .config import Config
from .bot import Bot


def main():
    # Configure logging
    root_logger = logging.getLogger()
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(
        ColoredFormatter("%(log_color)s%(levelname)-8s%(reset)s %(message)s"))
    root_logger.addHandler(root_handler)
    root_logger.setLevel(logging.DEBUG)

    loop = get_event_loop()

    conf = Config()
    conf.from_module('config')
    for network in conf.networks:
        print(network)
        bot = Bot(network, loop=loop)
        bot.run()

    loop.run_forever()
    loop.close()

main()
