# seabird

[![Build Status](https://drone.coded.io/api/badges/seabird/pyseabird/status.svg)](https://drone.coded.io/belak/seabird)

AKA the bot formerly known as the bot formerly known as seabird

## Goals

* Simple framework
* Clean code
* Only stdlib in core (irc portion)

## Setup

Required dependencies for core:

* python3.5 or greater

Install python plugin dependencies:

* pip install -r requirements.txt

The default distribution of seabird needs to be configured before it will do
anything. It will import the config module. The simplest option is to copy the
sample file provided at [config.dist.py](config.dist.py) to config.py, though
the important settings are outlined below:

### Basic settings

| Setting        | Required | Description                                             |
|----------------+----------+---------------------------------------------------------|
| NICK           | Yes      | IRC nickname                                            |
| PASS           |          | IRC password                                            |
| USER           | Yes      | IRC username                                            |
| NAME           | Yes      | IRC full name                                           |
| HOST           | Yes      | Hostname of the IRC server to connect to                |
| PORT           | Yes      | Port of the IRC server to connect to                    |
| CMDS           |          | List of commands to run after a welcome msg is received |
| PLUGIN_CLASSES |          | List of plugin classes to load                          |
| PLUGIN_MODULES |          | List of plugin modules to load                          |
| SSL            |          | True if the server needs SSL, False otherwise           |
| SSL_VERIFY     |          | True if the server has a valid cert, False otherwise    |

### Plugin settings

| Setting      | Required for plugin  | Description                                 |
|--------------+----------------------+---------------------------------------------|
| PREFIX       | For commands to work | Prefix to look for in messages for commands |
| FORECAST_KEY | Weather              | API key for forecast.io                     |
| DB_URI       | DB, karma, weather   | SQLAlchemy Database URI                     |

### Running seabird

seabird can be run with the command `python -m seabird`

## asyncio

In order to start background processing, simply grab the event loop and add a
task. Events will be processed one at a time, but when you create a task it will
fall back to the main event loop. This allows IRC messages to be processed in
the order they come in, but still makes it possible to move time consuming
operations into the background.

As an example:

``` python
async def callback(msg):
    print('do a thing')

loop = asyncio.get_event_loop()
loop.create_task(callback(msg))
```
