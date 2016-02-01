from .config import Config
from .bot import Bot

def main():
    conf = Config()
    conf.from_module('config')
    bot = Bot(conf)
    bot.run()

main()
