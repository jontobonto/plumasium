from redbot.core.bot import Red

from .dobble import Dobble


async def setup(bot: Red):
    await bot.add_cog(Dobble(bot))
