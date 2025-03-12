import asyncio
import io
import json
import logging
from contextlib import suppress
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Tuple, TypedDict

import discord
from discord import app_commands
from discord.ext import tasks
from redbot.core import Config, commands

from sticky.views import StickyButtonModal, StickySetModal
import discord.types.embed as eT

if TYPE_CHECKING:
    from redbot.core.bot import Red

log = logging.getLogger("sticky")

I = discord.Interaction["Red"]


class Sticky(TypedDict):
    channel_id: int
    last_message_id: int

    current_count: int
    max_count: int

    content: Optional[str]
    embeds: list[eT.Embed]


class Sticky(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot: "Red" = bot
        self.update_queue: list[discord.TextChannel] = []

        self.settings = Config.get_conf(
            cog_instance=self,
            identifier=2034700476555037629,
        )

        self.settings.register_channel(stickys=[])

        self.sticky_settings: dict[int, dict[int, list[Sticky]]] = {}

    async def _create_cache(self):
        self.sticky_settings = {}
        data: dict[int, dict] = await self.settings.all_channels()

        delete = []

        for channel_id, channel_data in data.items():
            channel = self.bot.get_channel(channel_id)

            if not channel:
                delete.append(channel_id)
                continue

            guild_dict = self.sticky_settings.get(channel.guild.id, {})
            channel_stickys = guild_dict.get(channel.id, [])
            channel_stickys.append(channel_data)
            self.sticky_settings[channel.guild.id][channel.id]

    async def cog_load(self):
        await self._create_cache()

    _sticky = app_commands.Group(
        name="sticky",
        description="Manage sticky messages",
        guild_only=True,
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @_sticky.command(name="add")
    async def _sticky_add(self, interaction: I, channel: discord.TextChannel)