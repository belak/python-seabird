from seabird.decorators import event
from seabird.plugin import Plugin


class WelcomePlugin(Plugin):
    def __init__(self, bot):
        pass

    @event('001')
    def welcome(self, bot, event):
        print('Welcome!')
