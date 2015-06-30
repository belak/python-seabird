import random
import re

from seabird.decorators import command, event
from seabird.plugin import Plugin


class CoinPlugin(Plugin):
    _coin_names = ['heads', 'tails']

    @command
    def coin(self, bot, event):
        """[heads|tails]

        Guess the coin flip. If you guess wrong, you're out!
        """
        if event.trailing not in CoinPlugin._coin_names:
            names = ', '.join(CoinPlugin._coin_names)
            bot.mention_reply(event,
                              "That's not a valid coin side."
                              "Options are: %s" % names)
            return

        answer = random.randint(0, len(CoinPlugin._coin_names)-1)
        if CoinPlugin._coin_names[answer] == event.trailing:
            bot.mention_reply(event, "Lucky guess!")
        else:
            bot.write(('KICK', event.args[0], event.prefix.name),
                      trailing="Sorry! Better luck next time!")


class DicePlugin(Plugin):
    dice_re = re.compile('(?:^|\b)(\d*)d(\d+)\b')

    @event('PRIVMSG')
    def dice_callback(self, bot, event):
        for match in DicePlugin.dice_re.finditer(event.trailing):
            print(match.group(1))
            print(match.group(2))


class RoulettePlugin(Plugin):
    def __init__(self, bot):
        self._channel_counter = {}
        self._gun_size = bot.config.get('ROULETTE_GUN_SIZE', 6)

    @command
    def roulette(self, bot, event):
        """Click... click... BANG!"""
        rounds_left = self._channel_counter.get(event.args[0], -1)
        if rounds_left == -1:
            bot.reply(event, "Reloading the gun.")
            rounds_left = random.randint(1, 6)

        rounds_left -= 1
        if rounds_left <= 0:
            bot.reply(event, "Bang!")
            bot.write(('KICK', event.args[0], event.prefix.name))
        else:
            bot.reply(event, "Click!")

        self._channel_counter[event.args[0]] = rounds_left


class MentionsPlugin(Plugin):
    @event('PRIVMSG')
    def mentions(self, bot, event):
        if not event.trailing.startswith(bot.current_nick + ': '):
            return

        vals = {
            'ping': 'pong',
            'scoobysnack': 'Scooby Dooby Doo!',
            'scooby snack': 'Scooby Dooby Doo!',
            'botsnack': ':)',
            'bot snack': ':)',
        }

        trailing = event.trailing[len(bot.current_nick)+2:].strip().lower()
        if trailing not in vals:
            return

        bot.mention_reply(event, vals[trailing])
