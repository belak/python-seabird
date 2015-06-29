# seaprince

AKA The Bot Formerly Known As Seabird

## Goals

* Simple framework
* Performant (when it needs to be)
* Clean code
* Only stdlib in core (irc portion)
* Way to add additional data to the bot object (like a db) as a plugin
* Similar to flask?

## Event types

* Command
* Message
* Raw event
* Scheduled events
  * Periodic events
  * At a specific time

## API

### Decorators

Event registration

* command
* event
* interval
* mention
* nick_command
* plugin

Limitations

* rate
* require_chanmsg
* require_privmsg

Modifications

* threaded

### Sample

```python
# utils.py
def decorator(func):
	@functools.wraps(func)
	def actual_decorator(*args, **kwargs):
		if len(args) == 1 && callable(args[0]):
			return func(args[0])
		else:
			return func
# init.py
bot = SeaPrince()
bot.config.from_object('config')

# plugins/roulette.py
import random
from . import bot

@bot.plugin
class Roulette():
	_gun_size = None
	_channel_counter = {}

	def __init__(self, bot, **kwargs):
		self._gun_size = bot.config.get('ROULETTE_GUN_SIZE', 6)

	@bot.command
	def roulette(self, bot, event):
		rounds_left = self._channel_counter.get(event.channel, -1)
		if rounds_left == -1:
			event.reply("Reloading the gun.")
			rounds_left = random.randint(1, 6)

		rounds_left -= 1
		if rounds_left <= 0:
			event.reply("Bang!")
		else:
			event.reply("Click!")
		self._channel_counter[event.channel] = rounds_left
```
