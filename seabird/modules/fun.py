import random
import re

from seabird.plugin import Plugin, CommandMixin


class CoinPlugin(Plugin, CommandMixin):
    _coin_names = ['heads', 'tails']

    def cmd_coin(self, msg):
        """[heads|tails]

        Guess the coin flip. If you guess wrong, you're out!
        """
        if msg.trailing not in CoinPlugin._coin_names:
            names = ', '.join(CoinPlugin._coin_names)
            self.bot.mention_reply(msg,
                                   "That's not a valid coin side. "
                                   "Options are: {}".format(names))
            return

        choice = random.choice(CoinPlugin._coin_names)
        if choice == msg.trailing:
            self.bot.mention_reply(msg, "Lucky guess!")
        else:
            self.bot.write('KICK', msg.args[0], msg.prefix.name,
                           "Sorry! Better luck next time!")


class DicePlugin(Plugin):
    dice_re = re.compile(r'(?:^|\b)(\d*)d(\d+)\b')

    def irc_privmsg(self, msg):
        total_count = 0
        all_rolls = []
        for match in DicePlugin.dice_re.finditer(msg.trailing):
            dice_count = int(match.group(1))
            dice_magnitude = int(match.group(2))

            total_count += dice_count

            if dice_count < 1:
                # Not enough dice
                self.bot.mention_reply(
                    msg,
                    '{} is not a valid number of dice.'.format(dice_count))
                return

            if dice_magnitude < 2:
                self.bot.mention_reply(
                    msg,
                    '{} is not a valid die size.'.format(dice_magnitude))
                return

            if dice_magnitude > 100:
                self.bot.mention_reply(
                    msg,
                    'Die of size {} is too large'.format(dice_magnitude))
                return

            if total_count > 100:
                self.bot.mention_reply(msg, 'Too many dice')
                return

            rolls = ['{}d{}:'.format(dice_count, dice_magnitude)]
            for _ in range(dice_count):
                rolls.append(str(random.randint(1, dice_magnitude)))

            all_rolls.append(' '.join(rolls))

        if all_rolls:
            self.bot.mention_reply(msg, ', '.join(all_rolls))


class RoulettePlugin(Plugin, CommandMixin):
    def __init__(self, bot):
        super().__init__(bot)

        self._channel_counter = {}
        self._gun_size = self.bot.config.get('ROULETTE_GUN_SIZE', 6)

    def cmd_roulette(self, msg):
        """Click... click... BANG!"""
        rounds_left = self._channel_counter.get(msg.args[0], -1)
        if rounds_left <= 0:
            self.bot.reply(msg, "Reloading the gun.")
            rounds_left = random.randint(1, self._gun_size)

        rounds_left -= 1
        if rounds_left <= 0:
            self.bot.reply(msg, "Bang!")
            self.bot.write('KICK', msg.args[0], msg.identity.name)
        else:
            self.bot.reply(msg, "Click!")

        self._channel_counter[msg.args[0]] = rounds_left


class MentionsPlugin(Plugin):
    def irc_privmsg(self, msg):
        if not msg.trailing.startswith(self.bot.current_nick + ': '):
            return

        vals = {
            'ping': 'pong',
            'scoobysnack': 'Scooby Dooby Doo!',
            'scooby snack': 'Scooby Dooby Doo!',
            'botsnack': ':)',
            'bot snack': ':)',
        }

        trailing = msg.trailing[len(self.bot.current_nick)+2:].strip().lower()
        if trailing not in vals:
            return

        self.bot.mention_reply(msg, vals[trailing])
