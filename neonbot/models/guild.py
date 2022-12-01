from __future__ import annotations

from typing import Union

import discord

from .model import Model


class Guild(Model):
    servers = {}

    def __init__(self, guild_id: int) -> None:
        super().__init__()

        self.guild_id = guild_id
        self.table = "servers"
        self.where = {"server_id": str(guild_id)}

    @staticmethod
    def get_instance(guild_id: Union[discord.Guild, int]):
        guild_id = int(guild_id)

        if guild_id not in Guild.servers.keys():
            Guild.servers[guild_id] = Guild(guild_id)

        return Guild.servers[guild_id]

    async def create_default_collection(self):
        await self.refresh()

        if self.get() is None:
            await self.db.servers.insert_one({
                "server_id": str(self.guild_id),
                "channel_id": None,
                "playlist_url": None
            })
