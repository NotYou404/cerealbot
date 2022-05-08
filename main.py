import discord
from discord.ext import commands

import asyncio
import dotenv
import os
import sys


class Cerealbot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(".", "c!", "kekw", "plz"),
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            intents=discord.Intents.all(),
            status=discord.Status.idle,
            activity=discord.Activity(
                name="starting up...", type=discord.ActivityType.playing
            ),
        )

    def setup(self):
        self.load_extension("cogs.administrative")


async def main():
    dotenv.load_dotenv()
    TOKEN = os.getenv("TOKEN")

    bot = Cerealbot()
    bot.setup()
    await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down the Bot without unloading.")
        sys.exit()
