import re

from sqlalchemy import Column, Integer, String

from seabird.plugin import Plugin, CommandMixin

from .db import Base, DatabasePlugin


class Karma(Base):
    __tablename__ = 'karma'

    name = Column(String, primary_key=True)
    score = Column(Integer, default=0)


class KarmaPlugin(Plugin, CommandMixin):
    regex = re.compile(r'([^\s]+)(\+\+|--)(?:\s|$)')

    def __init__(self, bot):
        super().__init__(bot)

        self.db = self.bot.load_plugin(DatabasePlugin)

    def cmd_karma(self, msg):
        normalized_item = msg.trailing.lower()
        with self.db.session() as session:
            score = Karma.score.default.arg

            k = session.query(Karma).get(normalized_item)
            if k:
                score = k.score

            self.bot.reply(msg, "%s's karma is %d" % (msg.trailing, score))

    def irc_privmsg(self, msg):
        if not self.bot.from_channel(msg):
            return

        if self.regex.match(msg.trailing):
            with self.db.session() as session:
                for (item, operation) in self.regex.findall(msg.trailing):
                    normalized_item = item.lower()

                    k, _ = session.get_or_create(Karma, name=normalized_item)

                    # Figure out if we need to add or subtract
                    diff = -1
                    if operation == '++':
                        diff = 1

                    # Update the model
                    k.score = Karma.score + diff
                    session.add(k)
                    session.flush()

                    k = session.query(Karma).get(normalized_item)
                    self.bot.reply(msg,
                                   "%s's karma is now %d" % (item, k.score))
