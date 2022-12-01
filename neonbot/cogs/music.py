import random
import re
import shutil
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from i18n import t

from neonbot import bot
from neonbot.classes.embed import Embed
from neonbot.classes.player import Player
from neonbot.classes.spotify import Spotify
from neonbot.classes.youtube import Youtube
from neonbot.utils.constants import ICONS, YOUTUBE_REGEX, SPOTIFY_REGEX, YOUTUBE_TMP_DIR


async def in_voice(interaction: discord.Interaction) -> bool:
    if await bot.is_owner(interaction.user) and interaction.command.name == "reset":
        return True

    if not interaction.user.voice:
        await interaction.response.send_message(embed=Embed("You need to be in the channel."), ephemeral=True)
        return False
    return True


async def has_player(interaction: discord.Interaction) -> bool:
    player = await Player.get_instance(interaction)

    if not player.connection:
        await interaction.response.send_message(embed=Embed("No active player."), ephemeral=True)
        return False
    return True


class Music(commands.Cog):
    @app_commands.command(name='radio')
    @app_commands.describe(url='Enter url...')
    @app_commands.check(in_voice)
    @app_commands.guild_only()
    async def radio(
        self,
        interaction: discord.Interaction,
        url: Optional[str] = None
    ):
        """Searches the url or the keyword and add it to queue."""
        player = await Player.get_instance(interaction)

        if not url:
            if player.settings.get('playlist_url'):
                url = player.settings.get('playlist_url')
            else:
                await interaction.response.send_message(embed=Embed(t("music.invalid_url")), ephemeral=True)
                return

        if not player.connection:
            await player.connect()
            await interaction.response.send_message(
                embed=Embed(t("music.player_connected", channel=interaction.channel.mention))
            )
        else:
            shutil.rmtree(YOUTUBE_TMP_DIR, ignore_errors=True)
            await player.reset()

        if re.search(YOUTUBE_REGEX, url):
            await Youtube(interaction).search_url(url)
        elif re.search(SPOTIFY_REGEX, url):
            await Spotify(interaction).search_url(url)

        await player.settings.update({'playlist_url': url})

        random.shuffle(player.queue)
        await player.play()

    @app_commands.command(name='nowplaying')
    @app_commands.check(in_voice)
    @app_commands.guild_only()
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        """Displays in brief description of the current playing."""

        player = await Player.get_instance(interaction)

        if not player.connection or not player.connection.is_playing():
            await interaction.response.send_message(embed=Embed(t('music.no_song_playing')), ephemeral=True)
            return

        now_playing = player.now_playing

        embed = Embed()
        embed.add_field(t('music.nowplaying.uploader'), now_playing['uploader'])
        embed.add_field(t('music.nowplaying.upload_date'), now_playing['upload_date'])
        embed.add_field(t('music.nowplaying.duration'), now_playing['formatted_duration'])
        embed.add_field(t('music.nowplaying.views'), now_playing['view_count'])
        embed.add_field(t('music.nowplaying.description'), now_playing['description'], inline=False)
        embed.set_author(
            name=now_playing['title'],
            url=now_playing['url'],
            icon_url=ICONS['music'],
        )
        embed.set_thumbnail(url=now_playing['thumbnail'])
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='bind')
    @app_commands.check(in_voice)
    @app_commands.guild_only()
    async def bind(self, interaction: discord.Interaction, channel: Optional[discord.VoiceChannel] = None):
        player = await Player.get_instance(interaction)

        await player.settings.update({'channel_id': channel.id if channel else interaction.channel.id})
        await interaction.response.send_message(
            embed=Embed(t('music.channel_bind', channel=channel.mention))
        )


# noinspection PyShadowingNames
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music())
