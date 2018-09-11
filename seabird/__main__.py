import asyncio
import logging
import os

from colorlog import ColoredFormatter

from .config import Config
from .bot import Bot


def main():
    # Configure logging
    root_logger = logging.getLogger()
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(
        ColoredFormatter("%(log_color)s%(levelname)-8s%(reset)s %(message)s")
    )
    root_logger.addHandler(root_handler)
    root_logger.setLevel(logging.DEBUG)

    config_module = os.getenv("SEABIRD_CONFIG_MODULE", "config")
    loop = asyncio.get_event_loop()

    conf = Config()
    conf.from_module(config_module)

    bot = Bot(conf, loop=loop)
    bot.run()


main()
