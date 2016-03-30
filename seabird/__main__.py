from asyncio import get_event_loop
from logging.config import dictConfig

# Configure logging. Note that this needs to come *before* any imports that use
# the logging package because it's annoying.
LOGGING = {
    'version': 1,
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'colored',
        },
    },
    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
        },
    },
}
dictConfig(LOGGING)

from .config import Config
from .bot import Bot


def main():
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
