import logging 
from typing import TYPE_CHECKING

import discord
from redbot.core import Config, app_commands, commands

if TYPE_CHECKING:
    from redbot.core.bot import Red

log = logging.getLogger("dobble")

class Dobble(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot = bot