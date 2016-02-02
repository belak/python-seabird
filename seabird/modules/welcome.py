from seabird.decorators import event
from seabird.plugin import Plugin


class WelcomePlugin(Plugin):
    @event('001')
    def welcome(self, _):
        print('Welcome!')
