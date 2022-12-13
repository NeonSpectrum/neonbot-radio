import asyncio
import re
import sys
from glob import glob
from os import sep
from time import time
from typing import Optional, Tuple, Any, List

import discord
from aiohttp import ClientSession, ClientTimeout
from discord.ext import commands
from discord.utils import oauth_url
from envparse import env
from i18n import t

from . import __version__
from .classes.database import Database
from .classes.embed import Embed
from .models.guild import Guild
from .utils import log
from .utils.constants import PERMISSIONS


class NeonBot(commands.Bot):
    def __init__(self):
        self.owner_ids = set(env.list("OWNER_IDS", default=[], subcast=int))
        self.user_agent = f"NeonBot v{__version__}"
        self.loop = asyncio.get_event_loop()

        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents, command_prefix='.')

        self.db = Database(self)
        self._settings = None
        self.app_info: Optional[discord.AppInfo] = None
        self.owner_guilds = env.list('OWNER_GUILD_IDS', default=[], subcast=int)
        self.session: Optional[ClientSession] = None

    @property
    def settings(self):
        return self._settings.get()

    def get_presence(self) -> Tuple[discord.Status, discord.Activity]:
        activity_type = self.settings.get('activity_type').lower()
        activity_name = self.settings.get('activity_name')
        status = self.settings.get('status')

        return (
            discord.Status[status],
            discord.Activity(
                name=activity_name, type=discord.ActivityType[activity_type]
            ),
        )

    async def setup_hook(self):
        self.db.initialize()
        self._settings = await self.db.get_settings()
        self.status, self.activity = self.get_presence()
        self.session = ClientSession(timeout=ClientTimeout(total=30))

        await self.add_cogs()

        guilds = [guild async for guild in self.fetch_guilds()]

        # await self.sync_command()

        # This copies the global commands over to your guild.
        # await asyncio.gather(*[self.sync_command(guild) for guild in guilds])

        await self.db.get_guilds(guilds)
        self.loop.create_task(self.autoplay(guilds))

    async def sync_command(self, guild: Optional[discord.Guild] = None):
        await self.tree.sync(guild=guild)
        log.info(f"Command synced to: {guild}")

    async def add_cogs(self):
        files = sorted(glob(f"neonbot{sep}cogs{sep}[!_]*.py"))
        extensions = [re.split(r"[{0}.]".format(re.escape(sep)), file)[-2] for file in files]
        start_time = time()

        print(file=sys.stderr)

        for extension in extensions:
            log.info(f"Loading {extension} cog...")
            await self.load_extension("neonbot.cogs." + extension)

        print(file=sys.stderr)

        log.info(f"Loaded {len(extensions)} cogs after {(time() - start_time):.2f}s\n")

    async def fetch_app_info(self) -> None:
        if not self.app_info:
            self.app_info = await self.application_info()

    async def send_invite_link(self, message: discord.Message) -> None:
        url = oauth_url(
            self.app_info.id,
            permissions=discord.Permissions(permissions=PERMISSIONS),
            scopes=('bot', 'applications.commands')
        )
        await message.channel.send(f"Bot invite link: {url}")
        log.info(f"Sent an invite link to: {message.author}")

    async def autoplay(self, guilds: List[discord.Guild]):
        from .classes.player import Player

        await self.wait_until_ready()

        for guild in guilds:
            settings = Guild.get_instance(guild.id)
            channel = await self.fetch_channel(settings.get('channel_id'))

            if not channel:
                continue

            if settings.get('autostart'):
                log.info('Executing autoplay for guild: ' + str(guild))
                message = await channel.send(embed=Embed('🔊 ' + t('music.autostart_started')), delete_after=5)
                ctx = await self.get_context(message)
                player = Player.get_instance_from_context(ctx)
                await player.autoplay(channel)

    async def send_response(self, interaction: discord.Interaction, *args, **kwargs):
        if not interaction.response.is_done():
            await interaction.response.send_message(*args, **kwargs)
        elif interaction.response.type in (discord.InteractionResponseType.deferred_message_update,
                                           discord.InteractionResponseType.deferred_channel_message):
            await interaction.followup.send(*args, **kwargs)
        else:
            await interaction.edit_original_response(*args, view=None, **kwargs)

    async def send_to_owner(self, *args: Any, **kwargs: Any) -> None:
        await self.get_user(self.app_info.owner.id).send(*args, **kwargs)

    async def close(self) -> None:
        await self.session.close()
        await super().close()

    async def start(self, *args, **kwargs) -> None:
        await super().start(*args, **kwargs)

    def run(self, *args, **kwargs):
        super().run(env.str('TOKEN'), *args, **kwargs)

    def _handle_ready(self) -> None:
        pass

    def set_ready(self):
        self._ready.set()
