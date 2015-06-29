from seabird.decorators import event


class WelcomePlugin:
    def __init__(self, bot):
        pass

    @event('001')
    def welcome(self, bot, event):
        print('Welcome!')
