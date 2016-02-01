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

Limitations

* rate
* require_chanmsg
* require_privmsg

Modifications

* threaded

### Sample Plugin

```python
class Roulette:
    def __init__(self, bot, **kwargs):
        self._channel_counter = {}
        self._gun_size = bot.config.get('ROULETTE_GUN_SIZE', 6)

    @command
    def roulette(self, bot, event):
        rounds_left = self._channel_counter.get(event.args[0], -1)
        if rounds_left == -1:
            bot.reply(event, "Reloading the gun.")
            rounds_left = random.randint(1, 6)

        rounds_left -= 1
        if rounds_left <= 0:
            bot.reply(event, "Bang!")
        else:
            bot.reply(event, "Click!")

        self._channel_counter[event.channel] = rounds_left
```
