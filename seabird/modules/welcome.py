from seabird.plugin import Plugin


class WelcomePlugin(Plugin):
    def irc_001(self, _):
        print("Welcome!")
