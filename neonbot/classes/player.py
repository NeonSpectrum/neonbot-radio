from __future__ import annotations

import asyncio
from typing import Union, List, Optional

import discord
from discord.ext import commands
from i18n import t

from neonbot import bot
from neonbot.classes.embed import Embed
from neonbot.classes.ytdl import Ytdl
from neonbot.enums.player_state import PlayerState
from neonbot.models.guild import Guild
from neonbot.utils import log
from neonbot.utils.constants import FFMPEG_OPTIONS
from neonbot.utils.exceptions import YtdlError


class Player:
    servers = {}

    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.loop = asyncio.get_event_loop()
        self.settings = Guild.get_instance(ctx.guild.id)
        self.queue = []
        self.current_queue = 0
        self.state = PlayerState.STOPPED

    @property
    def channel(self):
        return self.ctx.channel

    @property
    def connection(self) -> Optional[discord.VoiceClient]:
        return self.ctx.voice_client

    @staticmethod
    async def get_instance(interaction: discord.Interaction) -> Player:
        ctx = await bot.get_context(interaction)
        guild_id = ctx.guild.id

        if guild_id not in Player.servers.keys():
            Player.servers[guild_id] = Player(ctx)

        return Player.servers[guild_id]

    @staticmethod
    def get_instance_from_guild(guild: discord.Guild) -> Optional[Player]:
        return Player.servers.get(guild.id)

    def remove_instance(self) -> None:
        guild_id = self.ctx.guild.id

        if guild_id in Player.servers.keys():
            del Player.servers[guild_id]

    @property
    def now_playing(self) -> Union[dict, None]:
        try:
            return self.queue[self.current_queue]
        except IndexError:
            return None

    @now_playing.setter
    def now_playing(self, value) -> None:
        try:
            self.queue[self.current_queue] = value
        except IndexError:
            pass

    async def connect(self, channel: discord.VoiceChannel):
        if self.connection:
            return

        await channel.connect()

        log.cmd(self.ctx, t('music.player_connected', channel=channel))

    async def disconnect(self, force=True) -> None:
        if self.connection and self.connection.is_connected():
            await self.connection.disconnect(force=force)

    async def play(self) -> None:
        if not self.connection or not self.connection.is_connected() or self.connection.is_playing():
            return

        try:
            if not self.now_playing.get('stream'):
                ytdl_info = await Ytdl().process_entry(self.now_playing)
                info = ytdl_info.get_track(detailed=True)
                self.now_playing = {**self.now_playing, **info}

            source = discord.FFmpegPCMAudio(
                self.now_playing['stream'],
                before_options=None if not self.now_playing['is_live'] else FFMPEG_OPTIONS,
            )
            self.connection.play(source, after=lambda e: self.loop.create_task(self.after(error=e)))
            self.state = PlayerState.PLAYING

        except Exception as error:
            msg = str(error)

            if isinstance(error, discord.ClientException):
                if str(error) == 'Already playing audio.':
                    return
            elif not isinstance(error, YtdlError):
                msg = t('music.player_error')

            log.exception(msg, error)
            await self.channel.send(embed=Embed(msg))

    async def after(self, error=None):
        if error:
            log.error(error)
            return

        if self.state == PlayerState.STOPPED:
            return

        if self.current_queue >= len(self.queue) - 1:
            self.current_queue = 0
        else:
            self.current_queue += 1

        await self.play()

    async def reset(self):
        self.state = PlayerState.STOPPED
        self.connection.stop()

    def pause(self):
        if self.connection.is_paused() or not self.connection.is_playing():
            return

        self.connection.pause()

    def resume(self):
        if not self.connection.is_paused():
            return

        self.connection.resume()

    def add_to_queue(self, data: Union[List, dict]) -> None:
        if not data:
            return

        if not isinstance(data, list):
            data = [data]

        for info in data:
            self.queue.append(info)
