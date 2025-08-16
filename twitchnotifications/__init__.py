from typing import TYPE_CHECKING

from .twitchnotifications import TwitchNotifications

if TYPE_CHECKING:
    from redbot.core.bot import Red


async def setup(bot: "Red"):
    await bot.add_cog(TwitchNotifications(bot))
