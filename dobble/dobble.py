import logging
from typing import TYPE_CHECKING, Optional

from . import utils

import discord
from redbot.core import Config, app_commands, commands

from .utils import I

if TYPE_CHECKING:
    from redbot.core.bot import Red


log = logging.getLogger("dobble")


class Dobble(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot = bot

    @property
    def _utils(self):
        return utils

    @app_commands.command(name="dobble")
    async def _dobble(
        self,
        interaction: I,
    ):
        "Start a Dobble game with up to 8 players, including yourself."
        await utils.Game.start(interaction)
