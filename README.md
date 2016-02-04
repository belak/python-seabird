# seaprince

[![Build Status](https://travis-ci.org/belak/pyseabird.svg?branch=master)](https://travis-ci.org/belak/pyseabird)

AKA The Bot Formerly Known As Seabird

## Goals

* Simple framework
* Performant (when it needs to be)
* Clean code
* Only stdlib in core (irc portion)

## Event types

* Command
* Message
* Raw event
* Scheduled events
  * Periodic events
  * At a specific time

## asyncio

In order to start background processing, simply grab the event loop and add a
task. Events will be processed one at a time, but when you create a task it will
fall back to the main event loop. This allows IRC messages to be processed in
the order they come in, but still makes it possible to move time consuming
operations into the background.

## API

### Decorators

Event registration

* command
* event
* interval (not implemented yet)
* mention (not implemented yet)

Limitations (not implemented yet)

* rate
* require\_chanmsg
* require\_privmsg

Modifications

* threaded

### Sample Plugin

```python
from seabird.plugin import Plugin

class Roulette(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        self._channel_counter = {}
        self._gun_size = bot.config.get('ROULETTE_GUN_SIZE', 6)

    @command
    def roulette(self, event):
        rounds_left = self._channel_counter.get(event.args[0], -1)
        if rounds_left == -1:
            bot.reply(event, "Reloading the gun.")
            rounds_left = random.randint(1, 6)

        rounds_left -= 1
        if rounds_left <= 0:
            self.bot.reply(event, "Bang!")
        else:
            self.bot.reply(event, "Click!")

        self._channel_counter[event.channel] = rounds_left
```
