import discord
from discord.ext import commands

import asyncio
import validators
import youtube_dl


youtube_dl.utils.bug_reports_message = lambda: ""


ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True, volume=1.0):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # Takes the first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, volume=volume
        )


class Music(commands.Cog):
    """
    The Music Module!
    Contains all Music related features.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.emoji = "🎵"

    async def join_vc(self, ctx: discord.ApplicationContext):
        voice_state = ctx.user.voice
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_state:
            if not voice:
                await ctx.user.voice.channel.connect()
                return True
            else:
                return False

    async def leave_vc(self, ctx: discord.ApplicationContext):
        voice_state = ctx.user.voice
        voice: discord.VoiceClient = discord.utils.get(
            self.bot.voice_clients, guild=ctx.guild
        )
        if not voice:
            await ctx.respond("I'm not in any Voice Channel")
        else:
            if voice_state and voice_state.channel == voice.channel:
                await voice.disconnect()
                await ctx.respond(f"Left {voice.channel.mention}")
            else:
                await ctx.respond(
                    f"You must be connected to {voice.channel.mention} to do this"
                )

    async def play_url(
        self, ctx: discord.ApplicationContext, url: str, volume: float = 1.0
    ) -> YTDLSource:
        player = await YTDLSource.from_url(
            url, loop=self.bot.loop, stream=True, volume=volume
        )
        return player

    async def play_search(
        self, ctx: discord.ApplicationContext, search: str, volume: float = 1.0
    ) -> YTDLSource:
        player = None
        return player

    @discord.slash_command(
        name="join",
        description="Makes the Bot join your Voice Channel",
    )
    async def join(self, ctx: discord.ApplicationContext):
        result = await self.join_vc(ctx)
        if result:
            await ctx.respond(f"Joined {ctx.user.voice.channel.mention}")
        elif result == False:
            await ctx.respond(f"I'm already in {ctx.guild.me.voice.channel.mention}")
        else:
            await ctx.respond("You aren't connected to any Voice Channel")

    @discord.slash_command(
        name="leave",
        description="Makes the Bot leave your Voice Channel",
    )
    async def leave(self, ctx: discord.ApplicationContext):
        await self.leave_vc(ctx)

    @discord.slash_command(
        name="play",
        description="Play a Song from either an url or search",
    )
    async def play(
        self,
        ctx: discord.ApplicationContext,
        search: discord.Option(str, description="The url or search to look for"),
        volume: discord.Option(
            float,
            description="The Volume to play the sound. Min is 20, max is 200, default is 100",
            min_value=20,
            max_value=200,
        ) = 100,
    ):
        result = await self.join_vc(ctx)
        if result or (
            result is not None
            and ctx.guild.me.voice
            and ctx.user.voice.channel == ctx.guild.me.voice.channel
        ):
            if ctx.voice_client.is_playing():
                await ctx.respond("I am already playing in your channel")
                return
            volume /= 100

            await ctx.defer()
            if validators.url(search):
                try:
                    player = await self.play_url(ctx, search, volume)
                except:
                    await ctx.respond("Unsupported URL passed", ephemeral=True)
                    return
            else:
                player = await self.play_search()

            ctx.voice_client.play(
                player,
                after=lambda e: print(f"[ERROR] Encountered error while playing: {e}")
                if e
                else None,
            )

            embed = discord.Embed(color=discord.Color.blurple(), title=player.title)
            try:
                embed.url = player.data["webpage_url"]
            except:
                pass
            try:
                embed.set_author(
                    name=player.data["channel"], url=player.data["channel_url"]
                )
            except KeyError:
                pass
            try:
                embed.add_field(name="Views", value=player.data["view_count"])
                embed.add_field(name="Likes", value=player.data["like_count"])
            except KeyError:
                pass
            embed.add_field(name="Volume", value=f"{int(volume*100)}/200")
            try:
                embed.set_thumbnail(url=player.data["thumbnail"])
            except KeyError:
                pass
            await ctx.respond(embed=embed)

        elif result == False:
            await ctx.respond(f"I'm already in {ctx.guild.me.voice.channel.mention}")
        else:
            await ctx.respond("You aren't connected to any Voice Channel")


def setup(bot: commands.Bot):
    print("[SETUP] Music")
    bot.add_cog(Music(bot))


def teardown(bot: commands.Bot):
    print("[TEARDOWN] Music")
