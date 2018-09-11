import asyncio

import aiohttp

from seabird.plugin import Plugin, CommandMixin


ISSUES_URL = "https://api.github.com/repos/{}/{}/issues"


class IssuesPlugin(Plugin, CommandMixin):
    def __init__(self, bot):
        super().__init__(bot)

        self.username = bot.config["GITHUB_USERNAME"]
        self.token = bot.config["GITHUB_TOKEN"]
        self.target = bot.config.get("GITHUB_TARGET", ("belak", "python-seabird"))

    def cmd_issue(self, msg):
        loop = asyncio.get_event_loop()
        loop.create_task(self.issue_callback(msg))

    async def issue_callback(self, msg):
        assignee = None
        title = msg.trailing
        if title.startswith("@"):
            assignee, _, title = title[1:].partition(" ")

            if not assignee:
                self.bot.mention_reply(msg, "Issue asignee required with @ symbol")
                return

        if not title:
            self.bot.mention_reply(msg, "Issue title required")
            return

        data = {
            "title": title,
            "body": "Reported in {} by {}".format(msg.args[0], msg.identity.name),
        }

        if assignee:
            data["assignee"] = assignee

        headers = {
            "accept": "application/vnd.github.v3+json",
            "content-type": "application/vnd.github.v3+json",
            "user-agent": "seabird/0.1",
        }

        auth = aiohttp.BasicAuth(self.username, self.token)

        url = ISSUES_URL.format(self.target[0], self.target[1])
        async with aiohttp.ClientSession() as session, session.post(
            url, json=data, headers=headers, auth=auth
        ) as resp:
            if resp.status != 201:
                self.bot.mention_reply(msg, "Failed to file issue")
                return

            issue_data = await resp.json()
            self.bot.mention_reply(
                msg, "Issue created. {}".format(issue_data["html_url"])
            )
