import discord
from discord.ext import commands, tasks

from cogs import savefile

import asyncio
from datetime import datetime
import json
import os
import pathlib
import random
import string
import sys


class NotBotAdmin(commands.CheckFailure):
    pass


class IsBotBlacklisted(commands.CheckFailure):
    pass


def is_bot_admin():
    async def check(ctx: commands.Context):
        path = pathlib.Path(__file__).parent.parent
        with open(f"{path}{os.sep}files{os.sep}team.json", mode="r") as file:
            if ctx.author.id in json.loads(file.read()):
                return True
            else:
                raise NotBotAdmin("User isn't a Bot Administrator.")

    return commands.check(check)


def is_bot_blacklisted(ctx: commands.Context):
    path = pathlib.Path(__file__).parent.parent
    with open(f"{path}{os.sep}files{os.sep}blacklisted_user.json", mode="r") as file:
        if ctx.author.id not in json.loads(file.read()):
            return True
        else:
            raise IsBotBlacklisted("User is blacklisted from the Bot.")


class Administrative(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.unknown_error_message = savefile.get_save_file_value(
            "error_defaults.json"
        )["unknown"]
        self.bot.add_check(is_bot_blacklisted)

        def presences():
            while True:
                for presence in savefile.get_save_file_value("presences.json"):
                    yield presence

        self.change_presence_task.start(presences())
        self.restart_after.start(seconds=86400)

    @commands.Cog.listener(name="on_ready")
    async def on_ready(self):
        print(f"[READY] {self.bot.user} connected to Discord.")

    @tasks.loop(count=1)
    async def restart_after(self, seconds):
        await asyncio.sleep(seconds)
        for cog in list(self.bot.cogs.keys()):
            self.bot.unload_extension(f"cogs.{cog.lower()}")
        print(f"[AUTO] [RESTART] Automatic Restart after {seconds} seconds")
        os.execv(sys.executable, ["python"] + sys.argv)

    @tasks.loop(seconds=10)
    async def change_presence_task(self, presences):
        await self.bot.wait_until_ready()
        presence = next(presences)
        await self.bot.change_presence(
            activity=discord.Activity(
                name=presence,
                type=discord.ActivityType.playing,
            ),
            status=discord.Status.online,
        )

    @commands.Cog.listener(name="on_command_error")
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.NotOwner):
            await ctx.send(
                "Only the Bot Owner can use this command.", reference=ctx.message
            )
        elif isinstance(error, NotBotAdmin):
            await ctx.send(
                "Only a Bot Administartor can use this command.", reference=ctx.message
            )
        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.send(
                "This command requires an NSFW channel to run.", reference=ctx.message
            )

    @commands.command(
        name="add-bot-admin",
        brief="Add a Member to the Bots Administration Team",
        help="""Add a Member to the Bots Administration Team.
                Can only be used by the Bot Owner.""",
        usage="<user>",
    )
    @commands.is_owner()
    async def add_bot_admin(self, ctx: commands.Context, user: discord.User):
        class ModalAddBotTeamMember(discord.ui.Modal):
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.add_item(
                    discord.ui.InputText(
                        style=discord.InputTextStyle.short,
                        label="Enter Password",
                        min_length=8,
                        max_length=8,
                        required=True,
                    )
                )

            async def callback(self, interaction: discord.Interaction):
                if self.children[0].value != password:
                    old_message = interaction.message.content
                    await interaction.response.edit_message(
                        content=f"{old_message}\n\nWrong password, use the command again to retry."
                    )
                    return
                path = pathlib.Path(__file__).parent.parent
                with open(f"{path}{os.sep}files{os.sep}team.json", mode="r") as file:
                    team = json.loads(file.read())
                    if user.id in team:
                        await interaction.response.send_message(
                            f"{user} ({user.id}) is already a Bot Administrator."
                        )
                        return
                with open(f"{path}{os.sep}files{os.sep}team.json", mode="w") as file:
                    team.append(user.id)
                    file.write(json.dumps(team))
                await interaction.response.send_message(
                    f"Added {user} to the Bot Administrator Team."
                )

        class View(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(
                style=discord.ButtonStyle.blurple, label="Click to type password"
            )
            async def button_callback(
                self, button: discord.Button, interaction: discord.Interaction
            ):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(
                        "This is not for you.", ephemeral=True
                    )
                    return
                await self.on_timeout()
                modal = ModalAddBotTeamMember(title="Password Modal")
                await interaction.response.send_modal(modal)

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                await message.edit(view=self)

        password = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(8)
        )
        await ctx.author.send(password)
        message = await ctx.send(
            "Please Enter the Password I just sent to you.",
            view=View(),
            reference=ctx.message,
        )

    @add_bot_admin.error
    async def add_bot_admin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.UserNotFound):
            message = f"I couldn't find the user `{error.argument}`, please either provide a mention or an ID."
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"Missing Required argument `user`, please refer to `{ctx.prefix}help {ctx.command.name}`."
        else:
            message = self.unknown_error_message
        await ctx.send(message, reference=ctx.message)

    @commands.command(
        name="remove-bot-admin",
        brief="Removes someone from the Bot's Administartor Team",
        help="Remove someone from being Bot Administrator.",
        usage="<user>",
    )
    @commands.is_owner()
    async def remove_bot_admin(self, ctx: commands.Context, user: discord.User):
        class View(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(
                style=discord.ButtonStyle.blurple,
                label=f"Remove {user} from the Bot Admin Team",
            )
            async def button_callback(
                self, button: discord.Button, interaction: discord.Interaction
            ):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(
                        "This is not for you.", ephemeral=True
                    )
                    return
                await self.on_timeout()
                path = pathlib.Path(__file__).parent.parent
                with open(f"{path}{os.sep}files{os.sep}team.json", mode="r") as file:
                    team = json.loads(file.read())
                    if user.id not in team:
                        await interaction.response.send_message(
                            f"{user} ({user.id}) is not a Bot Administrator."
                        )
                        return
                with open(f"{path}{os.sep}files{os.sep}team.json", mode="w") as file:
                    team.pop(team.index(user.id))
                    file.write(json.dumps(team))
                await interaction.response.send_message(
                    f"Removed {user} from the Bot Administrator Team."
                )

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                await message.edit(view=self)

        message = await ctx.send(
            f"Are you sure you want to remove {user} from the Bot Administrator Team?",
            view=View(),
            reference=ctx.message,
        )

    @remove_bot_admin.error
    async def remove_bot_admin_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.UserNotFound):
            message = f"I couldn't find the user `{error.argument}`, please either provide a mention or an ID."
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"Missing Required argument `user`, please refer to `{ctx.prefix}help {ctx.command.name}`."
        else:
            message = self.unknown_error_message
        await ctx.send(message, reference=ctx.message)

    @commands.command(
        name="reload",
        brief="Reloads all Cogs",
        help="Reload all Cogs, used for debugging.",
        usage="",
    )
    @is_bot_admin()
    async def reload_bot(self, ctx: commands.Context):
        embed = discord.Embed(
            color=0x03FC07,
            title="Reloading...",
            description="Reloading Cog: ",
        )
        message = await ctx.send(embed=embed)
        print(f"[RELOAD] Reloading all Cogs, requested by {ctx.author}")
        for cog in list(self.bot.cogs.keys()):
            self.bot.reload_extension(f"cogs.{cog.lower()}")
            embed.description += cog
            await message.edit(embed=embed)
        print(f"[RELOAD] Reloaded all Cogs")
        embed.title = "Reloaded!"
        embed.description = "Reloaded all Cogs."
        embed.timestamp = datetime.utcnow()
        await message.edit(embed=embed)

    @reload_bot.error
    async def reload_bot_error(self, ctx: commands.Context, error):
        pass

    @commands.command(
        name="shutdown",
        brief="Stops the Bot",
        help="Shuts down the Bot by unloading all cogs and exiting.",
        usage="",
    )
    @is_bot_admin()
    async def shutdown(self, ctx: commands.Context):
        embed = discord.Embed(
            color=0xEB0905,
            title="Shutting down...",
            description="Unloading Cog: ",
        )
        print(f"[SHUTDOWN] Shutting down, requested by {ctx.author}")
        message = await ctx.send(embed=embed)
        for cog in list(self.bot.cogs.keys()):
            self.bot.unload_extension(f"cogs.{cog.lower()}")
            embed.description += cog
            await message.edit(embed=embed)
        print("[SHUTDOWN] Unloaded all Cogs and exited")
        embed.title = "Shut down."
        embed.description = "Successfully shut down."
        embed.timestamp = datetime.utcnow()
        await message.edit(embed=embed)
        sys.exit()

    @shutdown.error
    async def shutdown_error(self, ctx: commands.Context, error):
        pass

    @commands.command(
        name="restart",
        brief="Completely restarts the Bot",
        help="Completely restarts the Bot by unloading all cogs and restarting.",
        usage="",
    )
    @is_bot_admin()
    async def restart(self, ctx: commands.Context):
        embed = discord.Embed(
            color=0x03FC07,
            title="Restarting...",
            description="Unloading Cog: ",
        )
        print(f"[RESTART] Restarting, requested by {ctx.author}")
        message = await ctx.send(embed=embed)
        for cog in list(self.bot.cogs.keys()):
            self.bot.unload_extension(f"cogs.{cog.lower()}")
            embed.description += cog
            await message.edit(embed=embed)
        print("[RESTART] Unloaded all Cogs and restarting")
        embed.title = "Restarted."
        embed.description = "Restarted, please give me a second to get my cache ready."
        embed.timestamp = datetime.utcnow()
        await message.edit(embed=embed)
        os.execv(sys.executable, ["python"] + sys.argv)

    @restart.error
    async def restart_error(self, ctx: commands.Context, error):
        pass

    @commands.command(
        name="blacklist",
        aliases=("botban",),
        brief="Bans someone from using the Bot",
        help="Ban someone from using the Bot. This lasts unlimited until a staff member runs the unban command.",
        usage="<user> [reason]",
    )
    @is_bot_admin()
    async def blacklist(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str = "No Reason given.",
    ):
        class View(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(
                style=discord.ButtonStyle.red,
                label=f"Ban {user}",
                emoji="<:ban:925072659652431923>",
            )
            async def button_callback(
                self, button: discord.Button, interaction: discord.Interaction
            ):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(
                        "This is not for you.", ephemeral=True
                    )
                    return
                button.disabled = True
                await message.edit(view=self)
                path = pathlib.Path(__file__).parent.parent
                with open(
                    f"{path}{os.sep}files{os.sep}blacklisted_user.json", mode="r"
                ) as file:
                    file_content = json.loads(file.read())
                if user.id in file_content:
                    await interaction.response.send_message(
                        f"{user} is already Bot Banned."
                    )
                    return
                file_content.append(user.id)
                with open(
                    f"{path}{os.sep}files{os.sep}blacklisted_user.json", mode="w"
                ) as file:
                    file.write(json.dumps(file_content))
                print(f"[BLACKLIST] {user} has been blacklisted by {ctx.author}")
                await user.send(
                    f"You have been banned from the Bot for undefined time.\nReason: `{reason}`"
                )
                await interaction.response.send_message(
                    f"Blacklisted {user} with the reason `{reason}`"
                )

        embed = discord.Embed(
            description=f"""
Are you Sure you want to Blacklist {user} ({user.id})?
This completely locks them out of the Bot until someone uses `{ctx.prefix}botunban`."""
        )
        message = await ctx.send(embed=embed, view=View())

    @blacklist.error
    async def blacklist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.UserNotFound):
            await ctx.send(f"I couldn't find the user `{error.argument}`.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument `user`.")
        else:
            pass

    @commands.command(
        name="whitelist",
        aliases=("botunban",),
        brief="Whitelists someone from using the Bot if they have been blacklisted.",
        help="Whitelists someone who has been banned via the blacklist command so they can use the Bot again.",
        usage="<user> [reason]",
    )
    async def whitelist(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str = "No Reason given.",
    ):
        class View(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(
                style=discord.ButtonStyle.red,
                label=f"Unban {user}",
            )
            async def button_callback(
                self, button: discord.Button, interaction: discord.Interaction
            ):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(
                        "This is not for you.", ephemeral=True
                    )
                    return
                button.disabled = True
                await message.edit(view=self)
                path = pathlib.Path(__file__).parent.parent
                with open(
                    f"{path}{os.sep}files{os.sep}blacklisted_user.json", mode="r"
                ) as file:
                    file_content = json.loads(file.read())
                if user.id not in file_content:
                    await interaction.response.send_message(
                        f"{user} is not Bot Banned."
                    )
                    return
                file_content.pop(file_content.index(user.id))
                with open(
                    f"{path}{os.sep}files{os.sep}blacklisted_user.json", mode="w"
                ) as file:
                    file.write(json.dumps(file_content))
                print(f"[WHITELIST] {user} has been whitelisted by {ctx.author}")
                await user.send(
                    f"You have been unbanned from the Bot.\nReason: `{reason}`"
                )
                await interaction.response.send_message(
                    f"Whitelisted {user} with the reason `{reason}`"
                )

        embed = discord.Embed(
            description=f"""
Are you Sure you want to Whitelist {user} ({user.id})?
This will re-give them access to use the Bot."""
        )
        message = await ctx.send(embed=embed, view=View())

    @whitelist.error
    async def whitelist_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.UserNotFound):
            await ctx.send(f"I couldn't find the user `{error.argument}`.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing required argument `user`.")
        else:
            pass


def setup(bot: commands.Bot):
    print("[SETUP] Administrative")
    bot.add_cog(Administrative(bot))


def teardown(bot: commands.Bot):
    print("[TEARDOWN] Administrative")
