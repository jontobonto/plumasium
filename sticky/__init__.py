from typing import TYPE_CHECKING

from .sticky import Sticky

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(Sticky(bot))
