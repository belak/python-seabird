import asyncio
import aiohttp
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

from seabird.irc import Message
from seabird.plugin import Plugin, CommandMixin

from .trie import Trie


LEVEL_NAMES = [
    "total",
    "attack",
    "defence",
    "strength",
    "hitpoints",
    "ranged",
    "prayer",
    "magic",
    "cooking",
    "woodcutting",
    "fletching",
    "fishing",
    "firemaking",
    "crafting",
    "smithing",
    "mining",
    "herblore",
    "agility",
    "thieving",
    "slayer",
    "farming",
    "runecraft",
    "hunter",
    "construction",
]


class LevelMetadata(NamedTuple):
    """Represents level data for a player"""
    rank: int
    level: int
    experience: Optional[int] = None

    @classmethod
    def from_entry(cls, entry: str) -> "LevelMetadata":
        """Builds level metadata from a comma-separated string of integers"""
        return cls(*[int(p) for p in entry.split(",")])


class Item:
    def __init__(
        self,
        item_id: int,
        name: str,
        members: bool,
        average_price: int,
    ):
        self.item_id = item_id
        self.name = name
        self.members = members
        self.average_price = average_price

    @classmethod
    def from_json(self, item_data: Dict) -> "Item":
        return Item(
            item_data["id"],
            item_data["name"],
            item_data["members"],
            item_data["overall_average"],
        )

    def __str__(self):
        ret = f"{self.name}: {pretty_suffix(self.average_price)} GE"
        if self.members:
            ret += " (P2P)"
        return ret


def pretty_suffix(number: int) -> str:
    """Formats a number as an SI-suffixed string"""
    suffixes = [
        (1_000_000_000, 'B'),
        (1_000_000, 'M'),
        (1_000, 'K'),
    ]
    for threshold, suffix in suffixes:
        if number >= threshold:
            return f"{number / threshold:.1f}{suffix}"
    return str(number)


def pretty_thousands(number: int) -> str:
    """Formats a number with comma-separated thousands places"""
    ret = ""
    print('input: ', number)
    while number >= 1000:
        if ret:
            ret = f",{ret}"
        print('mod: ', number % 1000)
        print('div: ', number // 1000)
        ret = f"{number % 1000:03d}{ret}"
        number //= 1000

    if number > 0:
        if ret:
            ret = f",{ret}"
        ret = f"{number}{ret}"

    return ret


class OldSchoolRunescapePlugin(Plugin, CommandMixin):
    """Plugin for getting various bits of Old-School Runescape information"""

    ITEM_MATCH_LIMIT = 5

    HISCORE_URL = (
        "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws"
        "?player={player}"
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.names = None
        self.item_data = None

    def cmd_level(self, msg: Message) -> None:
        """
        <player> <skill>

        Returns the player's level in the given skill
        """
        loop = asyncio.get_event_loop()
        loop.create_task(
            self.level_callback(
                msg,
                "level",
                "{player} has level {value} {skill}",
                lambda v: str(v),
            )
        )

    def cmd_exp(self, msg: Message) -> None:
        """
        <player> <skill>

        Returns the player's experience in the given skill
        """
        loop = asyncio.get_event_loop()
        loop.create_task(
            self.level_callback(
                msg,
                "experience",
                "{player} has {value} experience in {skill}",
                pretty_suffix,
            )
        )

    def cmd_rank(self, msg: Message) -> None:
        """
        <player> <skill>

        Returns the player's rank in the given skill
        """
        loop = asyncio.get_event_loop()
        loop.create_task(
            self.level_callback(
                msg,
                "rank",
                "{player} is rank {value} in {skill}",
                pretty_thousands,
            )
        )

    def cmd_ge(self, msg: Message) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self.item_callback(msg))

    async def level_callback(
        self,
        msg: Message,
        prop: str,
        response_format: str,
        value_format: Callable[[int], str],
    ) -> None:
        """
        Common callback for player level information

        @param msg: Source IRC message for the command
        @param prop: Property to get from LevelMetadata
        @param response_format: Response string to populate information with
        @param value_format: Function to use to format level metadata value
        """
        if not msg.trailing:
            self.bot.mention_reply(msg, f"Usage: {prop} <player> <skill>")
            return

        args = msg.trailing.split()
        if len(args) != 2:
            self.bot.mention_reply(msg, f"Usage: {prop} <player> <skill>")
            return

        levels = await self.get_player_levels(args[0])
        if levels is None:
            self.bot.mention_reply(
                msg,
                f"Error getting level information for {args[0]}",
            )
            return

        skill = args[1].lower()

        if skill not in levels:
            self.bot.mention_reply(msg, f'Unknown skill "{skill}"')
            return

        value = getattr(levels[skill], prop)
        if value is None or value < 0:
            self.bot.mention_reply(
                msg,
                f"{args[0]}'s {prop} in {skill} is unknown",
            )
            return

        value_str = value_format(value)
        self.bot.mention_reply(
            msg,
            response_format.format(
                player=args[0],
                skill=skill,
                value=value_str,
            ),
        )

    async def get_player_levels(
        self,
        player: str,
    ) -> Optional[Dict[str, LevelMetadata]]:
        """Fetches all level metadata for the given player"""
        async with aiohttp.ClientSession() as session, session.get(
            self.HISCORE_URL.format(player=player)
        ) as resp:
            if resp.status != 200:
                return None

            data = await resp.text()
            levels = {}
            counter = 0
            for line in data.split("\n"):
                line = line.strip()
                if not line:
                    continue

                metadata = LevelMetadata.from_entry(line)
                if metadata.experience is None:
                    continue

                levels[LEVEL_NAMES[counter]] = metadata
                counter += 1

            return levels

    async def item_callback(self, msg: Message) -> None:
        if not msg.trailing:
            self.bot.mention_reply(msg, f"Usage: item <item_name>")
            return

        ret = await self.get_items()
        if ret is None:
            self.bot.mention_reply(msg, "Error fetching item information")
            return

        names, items = ret

        matched_names = names.words_for_prefix(msg.trailing)
        if not matched_names:
            self.bot.mention_reply(msg, "No items matched your search.")
            return

        if len(matched_names) > self.ITEM_MATCH_LIMIT:
            match_count = pretty_thousands(len(matched_names))
            self.bot.mention_reply(
                msg,
                f"Got {match_count} matches, which is more than the limit of "
                f"{self.ITEM_MATCH_LIMIT} matches. Please specify "
                "a stricter search term."
            )
            return

        if len(matched_names) > 1:
            self.bot.mention_reply(
                msg,
                f"{len(matched_names)} matches. Replying privately.",
            )
            for name in matched_names:
                self.bot.reply_to_user(msg, str(items[name]))

    async def get_items(self) -> Optional[Tuple[Trie, Dict[str, int]]]:
        if self.names is None or self.item_data is None:
            async with aiohttp.ClientSession() as session, session.get(
                "https://rsbuddy.com/exchange/summary.json"
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()
                ret = {}
                names = Trie()
                for item_id, item_data in data.items():
                    name = item_data["name"].lower()
                    ret[name] = Item.from_json(item_data)
                    names.add_word(name)

                self.names = names
                self.item_data = ret

        return self.names, self.item_data
