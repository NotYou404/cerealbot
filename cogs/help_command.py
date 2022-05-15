import discord
from discord.ext import commands

BUTTON_EMOJI_LEFT2 = "<:arrowsleft:947823526008737792>"
BUTTON_EMOJI_LEFT1 = "<:arrowleft:947823526356877332>"
BUTTON_EMOJI_RIGHT1 = "<:arrowright:947823526163939388>"
BUTTON_EMOJI_RIGHT2 = "<:arrowsright:947823525887111179>"
REPLY_EMOJI = "<:reply:938487139442786405>"


class Help_command(commands.Cog):
    """
    [hidden] The Cog holding the help command.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="help",
        brief="The help command",
        help="The help command",
        usage="<command|cog> [page]",
    )
    async def help_command(self, ctx: commands.Context, arg: str = None, page: int = 1):
        help = Help(bot=self.bot, ctx=ctx)
        await help.send_help(channel=ctx.channel, search=arg, page=page)


class Help:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self.ctx = ctx

    async def send_help(
        self,
        channel: discord.abc.Messageable,
        search: str,
        page: int,
        msg_to_edit: discord.Message = None,
    ) -> None:
        bot = self.bot
        ctx = self.ctx

        class View(discord.ui.View):
            def __init__(self, select_only: bool, page: int = 1, max_page: int = 1):
                super().__init__(timeout=60)

                class Select(discord.ui.Select):
                    def __init__(self):
                        options = []
                        for key, value in bot.cogs.items():
                            if "[hidden]" in value.description:
                                continue
                            options.append(
                                discord.SelectOption(
                                    label=key.capitalize(),
                                    description=f"{key.capitalize()} module help",
                                    emoji=value.emoji,
                                )
                            )
                        super().__init__(options=options)

                    async def callback(self, interaction: discord.Interaction):
                        await interaction.response.defer()
                        help = Help(bot=bot, ctx=ctx)
                        await help.send_help(
                            channel=channel,
                            search=self.values[0],
                            page=1,
                            msg_to_edit=message,
                        )

                class Button(discord.ui.Button):
                    def __init__(self, emoji: str, page: int, max_page: int):
                        self.emoji_raw = emoji
                        self.page = page
                        self.max_page = max_page
                        super().__init__(style=discord.ButtonStyle.blurple, emoji=emoji)

                    async def callback(self, interaction: discord.Interaction):
                        await interaction.response.defer()
                        help = Help(bot=bot, ctx=ctx)
                        if self.emoji_raw == BUTTON_EMOJI_LEFT2:
                            self.page = 1
                        elif self.emoji_raw == BUTTON_EMOJI_LEFT1:
                            if self.page > 1:
                                self.page -= 1
                            else:
                                self.page = 1
                        elif self.emoji_raw == BUTTON_EMOJI_RIGHT1:
                            if self.page < self.max_page:
                                self.page += 1
                            else:
                                self.page = self.max_page
                        elif self.emoji_raw == BUTTON_EMOJI_RIGHT2:
                            self.page = self.max_page
                        await help.send_help(
                            channel=channel,
                            search=arg[0],
                            page=self.page,
                            msg_to_edit=message,
                        )

                self.add_item(Select())
                if not select_only:
                    self.add_item(Button(BUTTON_EMOJI_LEFT2, page, max_page))
                    self.add_item(Button(BUTTON_EMOJI_LEFT1, page, max_page))
                    self.add_item(Button(BUTTON_EMOJI_RIGHT1, page, max_page))
                    self.add_item(Button(BUTTON_EMOJI_RIGHT2, page, max_page))

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                await message.edit(view=self)

        if msg_to_edit:

            async def send(*args, **kwargs):
                return await msg_to_edit.edit(*args, **kwargs)

        else:

            async def send(*args, **kwargs):
                return await channel.send(*args, **kwargs)

        if search is None:
            view = View(select_only=True)
            message = await send(embed=self.default_help(), view=view)
        else:
            arg = self.verify_help_type(search)
            if arg is None:
                await send(self.none_help(search))
            elif isinstance(arg, commands.Command):
                await send(embed=self.get_command_help(arg))
            elif isinstance(arg, tuple):
                cog_help, max_page = self.get_cog_help(arg, page)
                view = View(select_only=False, page=page, max_page=max_page)
                message = await send(embed=cog_help, view=view)

    def get_cog_help(self, cog: tuple[str, commands.Cog], page: int) -> discord.Embed:
        commands_in_cog = cog[1].get_commands()
        commands_paged = []
        PAGE_LEN = 6
        for i in range(0, len(commands_in_cog), PAGE_LEN):
            commands_paged.append(commands_in_cog[i : i + PAGE_LEN])

        if page > len(commands_paged):
            page = len(commands_paged)
        elif page < 1:
            page = 1
        relevant_page = commands_paged[page - 1]
        embed = discord.Embed(
            color=discord.Color.embed_background("dark"),
            title=f"{cog[0].capitalize()} help",
            description=f"*{cog[1].description}*",
        )
        embed.set_footer(
            text=f"Page {page} of {len(commands_paged)}",
            icon_url=self.bot.user.avatar.url,
        )
        for command in relevant_page:
            embed.add_field(
                name=command.name,
                value=f"{REPLY_EMOJI} {command.brief}",
                inline=False,
            )
        return embed, len(commands_paged)

    def get_command_help(
        self, command: commands.Command | discord.SlashCommand
    ) -> discord.Embed:
        embed = discord.Embed(
            color=discord.Color.embed_background("dark"),
            title=f"{command.name.capitalize()} help",
            description=command.help,
        )
        aliases = list(map(lambda x: f"`{x}`", command.aliases))
        aliases.append(f"`{command.name}`")
        embed.add_field(name="Aliases", value=", ".join(list(aliases)), inline=False)
        space = " " if command.usage else ""
        embed.add_field(
            name="Usage",
            value=f"`{self.ctx.prefix}{command.name}{space}{command.usage}`",
            inline=False,
        )
        embed.set_footer(
            text="Usage Sytax: <required> [optional] <either this|or this>",
            icon_url=self.bot.user.avatar.url,
        )
        return embed

    def none_help(self, search: str) -> str:
        return f"No help topic found on search: {search}."

    def default_help(self) -> discord.Embed:
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title="Help is there",
            description=f"""
Please select a Module from the dropdown menu to get Module help.
Help syntax:
`{self.ctx.prefix}help <module> [page]`
`{self.ctx.prefix}help <command>`
""",
        )
        embed.add_field(
            name="🔗 Usefull links",
            value="""
[Support Discord](https://dsc.gg/cersmp) | [Website](https://cersmp.ml) | [Dashboard](https://cersmp.ml) | [Github](https://github.com/NotYou404/cerealbot)
""",
        )
        return embed

    def verify_help_type(
        self, arg: str
    ) -> commands.Command | tuple[str, commands.Cog] | None:
        arg = arg.lower()
        for key, value in self.bot.cogs.items():
            if "[hidden]" in value.description:
                continue
            if arg == key.lower():
                return (key, value)
        command = self.bot.get_command(arg)
        if command is not None:
            return command
        else:
            return None


def setup(bot: commands.Bot):
    print("[SETUP] Help command")
    bot.add_cog(Help_command(bot))


def teardown(bot: commands.Bot):
    print("[TEARDOWN] Help command")
