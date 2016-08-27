import asyncio
import logging
import os

from .bot import Bot
from .config import Config

LOG = logging.getLogger(__name__)


class BotManager:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.config = Config()

        # Load the config from the specified location.
        config_module = os.getenv('SEABIRD_CONFIG_MODULE', 'config')
        LOG.info('Loading config from module \'%s\'', config_module)
        self.config.from_module(config_module)

        self.networks = {}

    def start(self):
        for name, network_config in self.config.networks.items():
            print(name)
            bot = Bot(network_config, loop=self.loop)
            bot.run()

    def run(self):
        self.loop.run_forever()
        self.loop.close()
