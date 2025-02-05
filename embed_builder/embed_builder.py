import random
import logging
from typing import TYPE_CHECKING, Optional

from . import utils
from typing import TypedDict

import discord
from redbot.core import Config, app_commands, commands

if TYPE_CHECKING:
    from redbot.core.bot import Red

I = discord.Interaction["Red"]


class View(discord.ui.View):
    pass

class EmbedBuilderMainView(View):
    def __init__(self):
        super().__init__(timeout=timeout)


class Dobble(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot = bot


