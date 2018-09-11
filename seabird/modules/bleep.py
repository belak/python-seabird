from functools import lru_cache
import random
import re

from sqlalchemy import Column, String

from seabird.plugin import Plugin, CommandMixin

from .db import Base, DatabaseMixin


class Bleep(Base):
    __tablename__ = "bleep"

    bad_word = Column(String, primary_key=True)
    replacement = Column(String)


class BleepPlugin(Plugin, CommandMixin, DatabaseMixin):
    __disabled__ = True

    REPLIES = [
        'Hey, watch your mouth! Say "{}" instead.',
        'Pottymouth! We say "{}" in this channel.',
        'Uh oh, you should really say "{}" instead.',
        'Time to put a quarter in the jar! You should really use "{}" instead.',
    ]

    @lru_cache(maxsize=1)
    def _get_bleeps(self):
        """
        Gets a list of bleeped words and their replacements

        @return [Bleep] List of bleeps
        """
        with self.db.session() as session:
            query = session.query(Bleep)

            bleeps = query.all()

            # This call is necessary to use the retrieved bleeps outside the
            # scope of the with
            session.expunge_all()

            return bleeps

    def cmd_bleep(self, msg):
        """
        Begin to bleep `bad_word` with `replacement`.

        `bad_word` is args[0]
        `replacement` is args[1]
        """
        args = msg.trailing.lower().strip().split(" ")

        if len(args) < 2:
            self.bot.reply(msg, "Must supply a bad word and a replacement")
            return

        bad_word = args[0]
        replacement = args[1]

        with self.db.session() as session:
            bleep, _ = session.get_or_create(Bleep, bad_word=bad_word)

            bleep.replacement = replacement
            session.add(bleep)

        # Invalidate the cache on _get_bleeps so that we read the new value
        self._get_bleeps.cache_clear()
        self.bot.reply(
            msg, "Will now bleep out {} with {}".format(bad_word, replacement)
        )

    def irc_privmsg(self, msg):  # pylint: disable=arguments-differ
        super().irc_privmsg(msg)

        if not msg.from_channel:
            return

        trailing = msg.trailing.lower().strip()
        if trailing.startswith("{}bleep".format(self.bot.config["PREFIX"])):
            return

        words = trailing.split(" ")
        for bleep in self._get_bleeps():
            regex = re.compile(r"\b{}\b".format(bleep.bad_word))
            for word in words:
                if regex.match(word):
                    reply = random.choice(self.REPLIES)
                    self.bot.mention_reply(msg, reply.format(bleep.replacement))
