from redbot.core.bot import Red

from .attix import Attix


async def setup(bot: Red):
    await bot.add_cog(Attix(bot))
