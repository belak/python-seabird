from collections import defaultdict
import re

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import and_

from seabird.plugin import Plugin, CommandMixin

from .db import Base, DatabaseMixin


class MultiMention(Base):
    __tablename__ = "multimention"

    mmention_id = Column(Integer, primary_key=True)
    group_name = Column(String)
    nick = Column(String)

    __table_args__ = (UniqueConstraint("group_name", "nick", name="_group_name_nick"),)


class MultiMentionPlugin(Plugin, CommandMixin, DatabaseMixin):
    regex = re.compile(r"@(?P<group>[^\s]+)\b")

    def _get_mention_groups(self, group_name=None):
        """
        Gets a list of mention groups and optionally filters by group
        name

        @param string group_name Optional group name to filter on
        @return [MultiMention] List of mention groups
        """
        with self.db.session() as session:
            query = session.query(MultiMention)

            if group_name is not None:
                query.filter(MultiMention.group_name == group_name)

            mmentions = query.all()

            group_members = defaultdict(list)
            for mmention in mmentions:
                group_members[mmention.group_name].append(mmention.nick)

            if group_name is not None:
                return group_members[group_name]

            return group_members

    def _rm_mention(self, group_name, nicks=None):
        """
        Remove mention group with name `group_name`. If `nicks` is supplied,
        only remove `nicks` from mention group.

        @param string group_name Name of group to remove
        @param [string]? nicks Nicks to be removed from `group_name`
        """
        with self.db.session() as session:
            query = session.query(MultiMention)
            if nicks is None:
                query = query.filter(MultiMention.group_name == group_name)
            else:
                query = query.filter(
                    and_(
                        MultiMention.group_name == group_name,
                        MultiMention.nick.in_(nicks),
                    )
                )
            mmentions = query.all()
            for mmention in mmentions:
                session.delete(mmention)

    def _cmd_list(self, msg):
        """
        Show all groups and their members.
        """
        groups = self._get_mention_groups()
        if not groups:
            self.bot.reply(msg, "No groups have been added")
            return

        for group_name, members in groups.items():
            self.bot.reply(msg, "{}: {}".format(group_name, ", ".join(members)))

    def _cmd_show(self, msg, args):
        """
        Show members of a given group.

        `group_name` is args[0]
        """
        if not args:
            self.bot.reply(msg, 'Must supply group_name to "show" command')
            return

        group = self._get_mention_groups(group_name=args[0])
        if not group:
            self.bot.reply(msg, "Unknown group {}".format(args[0]))
            return

        self.bot.reply(msg, "{}: {}".format(args[0], ", ".join(group)))

    def _cmd_add(self, msg, args):
        """
        Add `nicks` to mention group named `group_name`.
        If `group_name` doesn't exist it will be created.

        `group_name` is args[0]
        `nicks` is args[1:]
        """
        if len(args) < 2:
            self.bot.reply(msg, 'Must supply group_name and nick to "show" command')
            return

        group_name = args[0]
        nicks = args[1:]

        successful_nicks = []
        for nick in nicks:
            try:
                mmention = MultiMention()
                mmention.group_name = group_name
                mmention.nick = nick
                with self.db.session() as session:
                    session.add(mmention)
                successful_nicks.append(nick)
            except IntegrityError:
                self.bot.reply(msg, "{} already contains {}".format(group_name, nick))
        self.bot.reply(
            msg, "Added {} to {}".format(", ".join(successful_nicks), group_name)
        )

    def _cmd_rm(self, msg, args):
        """
        Remove either members from a group or an entire group itself.

        `group_name` is args[0]
        `nicks` is args[1:]
        """
        if len(args) < 1:
            self.bot.reply(msg, 'Must at least supply group_name to "rm" command')
            return

        group_name = args[0]
        nicks = None
        if len(args) > 1:
            nicks = args[1:]

        self._rm_mention(group_name, nicks)
        if nicks is None:
            self.bot.reply(msg, "Deleted group {}".format(group_name))
        else:
            self.bot.reply(
                msg, "Removed {} from to {}".format(", ".join(nicks), group_name)
            )

    def cmd_mmention(self, msg):
        args = msg.trailing.lower().strip().split(" ")

        cmd = args[0]
        args.pop(0)

        if cmd == "":
            self.bot.reply(msg, "Must pass one of list|show|add|rm")
        elif cmd == "list":
            self._cmd_list(msg)
        elif cmd == "show":
            self._cmd_show(msg, args)
        elif cmd == "add":
            self._cmd_add(msg, args)
        elif cmd == "rm":
            self._cmd_rm(msg, args)
        else:
            self.bot.reply(msg, 'Unsupported command "{}"'.format(cmd))

    def irc_privmsg(self, msg):
        super().irc_privmsg(msg)

        if not msg.from_channel:
            return

        match = self.regex.match(msg.trailing)
        if match is not None:
            group_name = match.group("group")
            group = self._get_mention_groups(group_name=group_name)
            if not group:
                return

            self.bot.reply(msg, "{}: ^".format(", ".join(group)))
