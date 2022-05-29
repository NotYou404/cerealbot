import discord
from discord.ext import commands

from datetime import datetime
import time
import typing


class Utility(commands.Cog):
    """
    The Module containing Utility functions like a translator, Guild and User statistics or a Role assigner.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.emoji = "🛠"

    @commands.command(
        name="ping",
        brief="Get the Bot latency",
        help="Checks the Bot and Message latency.",
        usage="",
    )
    async def ping(self, ctx: commands.Context):
        start_time = time.time()
        message = await ctx.send("Testing Ping...")
        end_time = time.time()
        bot_latency = round(self.bot.latency * 1000)
        api_latency = round((end_time - start_time) * 1000)
        if bot_latency < 300 and api_latency < 550:
            color = 0x09FF00
        elif bot_latency < 600 and api_latency < 850:
            color = 0xFF6200
        else:
            color = 0xDE0000
        embed = discord.Embed(title="Pong!", colour=color, timestamp=datetime.utcnow())
        embed.add_field(name="Bot Latency", value=f"{bot_latency}ms")
        embed.add_field(
            name="API/Message Latency",
            value=f"{api_latency}ms",
        )
        if color == 0xFF6200 or color == 0xDE0000:
            embed.add_field(
                name="High Values",
                value="If the Bot latency is high the Bot is probably overloaded.\nIf the API Latency is high, Discord probably has some problems.\nIf you don't feel that the Bot is slow don't worry about high numbers, 1000ms is also just a second.",
            )

        embed.set_footer(text=f"Pong requested by {ctx.author}")
        await message.edit("", embed=embed)

    @ping.error
    async def ping_error(self, ctx: commands.Context, error):
        pass

    @commands.command(
        name="whois",
        brief="Get informations about a User",
        help="Receive informations and stats about a User.\nYou can also get their name via their ID.",
        usage="<user>",
    )
    async def whois(
        self, ctx: commands.Context, user: typing.Union[discord.User, discord.Member]
    ):
        embed = discord.Embed(color=user.accent_colour if user.accent_colour else 0)
        embed.set_author(name=user, icon_url=user.display_avatar)
        embed.set_thumbnail(url=user.display_avatar)
        embed.add_field(
            name="Account created",
            value=f"<t:{int(user.created_at.timestamp())}> (<t:{int(user.created_at.timestamp())}:R>)",
            inline=True,
        )
        view = None
        if member := ctx.guild.get_member(user.id):
            embed.add_field(
                name="Joined",
                value=f"<t:{int(member.joined_at.timestamp())}> (<t:{int(member.joined_at.timestamp())}:R>)",
                inline=True,
            )
            roles = map(lambda role: role.mention, member.roles[1:])
            roles_str = ", ".join(list(roles))
            if len(roles_str) > 1024:
                roles_str = "*Too many to display*"

                class View(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=60)

                    @discord.ui.button(label="Click to see Roles")
                    async def button_callback(
                        self,
                        button: discord.ui.Button,
                        interaction: discord.Interaction,
                    ):
                        roles = ", ".join(
                            list(map(lambda role: role.mention, member.roles[1:]))[::-1]
                        )
                        await interaction.response.send_message(roles, ephemeral=True)

                    async def on_timeout(self):
                        for child in self.children:
                            child.disabled = True
                        await message.edit(view=self)

                view = View()
            embed.add_field(
                name="Roles", value=roles_str if roles_str else "no roles", inline=False
            )
            permissions = iter(member.guild_permissions)
            permissions_str = []
            for permission in permissions:
                if permission[1]:
                    permissions_str.append(f"`{permission[0]}`")
            permissions_str = ", ".join(permissions_str)
            embed.add_field(
                name="Permissions",
                value=permissions_str if permissions_str else "no permissions",
                inline=False,
            )
        flags = iter(user.public_flags)
        flags_str = []
        for flag in flags:
            if flag[1]:
                flags_str.append(f"`{flag[0]}`")
        flags_str = ", ".join(flags_str)
        if len(flags_str):
            embed.add_field(name="User Flags", value=flags_str, inline=False)
        message = await ctx.send(embed=embed, view=view)

    @whois.error
    async def whois_error(self, ctx: commands.Context, error):
        pass


def setup(bot: commands.Bot):
    print("[SETUP] Utility")
    bot.add_cog(Utility(bot))


def teardown(bot: commands.Bot):
    print("[TEARDOWN] Utility")
