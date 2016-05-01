import logging

from colorlog import ColoredFormatter

from .manager import BotManager


def main():
    # Configure logging
    root_logger = logging.getLogger()
    root_handler = logging.StreamHandler()
    root_handler.setFormatter(
        ColoredFormatter("%(log_color)s%(levelname)-8s%(reset)s %(message)s"))
    root_logger.addHandler(root_handler)
    root_logger.setLevel(logging.DEBUG)

    # Start up the bot manager and the bots
    manager = BotManager()
    manager.start()
    manager.run()

main()
