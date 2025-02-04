import random
import logging
from typing import TYPE_CHECKING, Optional

from . import utils

import discord
from redbot.core import Config, app_commands, commands

if TYPE_CHECKING:
    from redbot.core.bot import Red

I = discord.Interaction["Red"]

_cards = [
    ["⚡", "🐬", "🔥", "🐶", "🥕", "🌙", "🎵", "🖊️"],
    ["🍃", "❓", "🔒", "⛄", "🕷️", "🖊️", "💀", "💧"],
    ["❗", "👋", "🔥", "🕯️", "🙋", "🐢", "🕷️", "🦓"],
    ["🚙", "💐", "👋", "🐶", "⛄", "🕶️", "🕰️", "🐦"],
    ["👁️", "❗", "🤡", "🧊", "🍾", "🐞", "🕶️", "🖊️"],
    ["⚓", "🍎", "❤️", "🕯️", "🖌️", "🕸️", "🖊️", "🐦"],
    ["🌳", "💣", "👋", "💡", "🗝️", "🖊️", "☯️", "🏁"],
    ["👻", "🧀", "🥕", "🕶️", "🕸️", "💀", "🦓", "🏁"],
    ["👻", "🐶", "🌵", "🐱", "🖌️", "🐞", "🕷️", "☯️"],
    ["⚓", "⚡", "🤡", "👻", "💡", "👄", "🐢", "⛄"],
    ["🚙", "🤡", "🔥", "🔨", "⛺", "🕸️", "💧", "☯️"],
    ["🍎", "💣", "🧊", "⛺", "🌵", "🎵", "⛄", "🦓"],
    ["⚡", "🐞", "🗝️", "❄️", "☀️", "🐦", "💧", "🦓"],
    ["🕯️", "👄", "🎵", "⛔", "🔒", "❄️", "🕶️", "☯️"],
    ["🌳", "🦕", "🔥", "🍾", "🧀", "🖌️", "❄️", "⛄"],
    ["🍎", "💐", "🤡", "🐬", "🐉", "❄️", "🕷️", "🏁"],
    ["💐", "🦕", "❓", "💡", "🙋", "🐞", "🎵", "🕸️"],
    ["🍾", "💡", "⛺", "🍀", "🥕", "⛔", "🕷️", "🐦"],
    ["🐉", "❓", "⛺", "🖌️", "🌙", "🐢", "🗝️", "🕶️"],
    ["🍃", "🐬", "👋", "❤️", "⛺", "🧀", "👄", "🐞"],
    ["👁️", "🍃", "💣", "🐶", "🍀", "🐢", "❄️", "🕸️"],
    ["⚓", "❗", "🦕", "🐶", "⛺", "🔒", "☀️", "🏁"],
    ["⚡", "💣", "🦕", "🔨", "❤️", "🐴", "🕶️", "🕷️"],
    ["👻", "⛺", "🙋", "🐴", "✂️", "❄️", "🖊️", "🕰️"],
    ["🌳", "🤡", "❓", "❤️", "🐶", "✂️", "⛔", "🦓"],
    ["🍃", "🤡", "🦕", "🌵", "🕯️", "🥕", "🗝️", "🕰️"],
    ["❗", "🌳", "🍃", "🐉", "👻", "🔨", "🎵", "🐦"],
    ["💐", "🧊", "🔥", "👻", "❤️", "🍀", "🔒", "🗝️"],
    ["👁️", "🐬", "💡", "🔨", "🖌️", "🔒", "🕰️", "🦓"],
    ["🚙", "🍃", "⚡", "🧊", "🖌️", "🙋", "⛔", "🏁"],
    ["⚓", "🌳", "🐬", "🌵", "🍀", "🙋", "🕶️", "💧"],
    ["👁️", "🐉", "❤️", "🙋", "🥕", "⛄", "☀️", "☯️"],
    ["👁️", "🔥", "❓", "🌵", "👄", "🐴", "🐦", "🏁"],
    ["🍎", "❗", "⚡", "❓", "🧀", "🍀", "🕰️", "☯️"],
    ["🍎", "🚙", "🌳", "🐞", "🥕", "🐴", "🐢", "🔒"],
    ["❗", "🐬", "🐱", "🐴", "⛔", "🗝️", "⛄", "🕸️"],
    ["🍾", "❤️", "🐱", "🎵", "🐢", "🕰️", "💧", "🏁"],
    ["⚓", "💣", "🐉", "🔥", "🐞", "⛔", "💀", "🕰️"],
    ["🌳", "🧊", "👄", "🌙", "☀️", "🕷️", "🕸️", "🕰️"],
    ["🚙", "🦕", "🐉", "🐱", "🍀", "👄", "🖊️", "🦓"],
    ["🐬", "🦕", "🧊", "✂️", "🐢", "💀", "🐦", "☯️"],
    ["🍎", "👁️", "🦕", "👋", "👻", "🌙", "⛔", "💧"],
    ["💐", "🔨", "🌵", "🧀", "⛔", "🐢", "☀️", "🖊️"],
    ["👁️", "🌳", "⚡", "💐", "⛺", "🐱", "🕯️", "💀"],
    ["🚙", "💣", "🐬", "🍾", "❓", "👻", "🕯️", "☀️"],
    ["🔨", "🕯️", "🍀", "🐞", "🌙", "✂️", "⛄", "🏁"],
    ["❗", "💐", "💣", "🖌️", "👄", "🥕", "✂️", "💧"],
    ["⚓", "👁️", "🚙", "🧀", "🎵", "✂️", "🗝️", "🕷️"],
    ["⚓", "🍃", "💐", "🍾", "🌙", "🐴", "☯️", "🦓"],
    ["🍎", "🍾", "🔨", "🐶", "👄", "🙋", "🗝️", "💀"],
    ["🐉", "🧊", "💡", "🐶", "🧀", "🕯️", "🐴", "💧"],
    ["🤡", "👋", "🖌️", "🍀", "🎵", "🐴", "☀️", "💀"],
    ["💣", "🤡", "🧀", "🐱", "🙋", "🌙", "🔒", "🐦"],
    ["🍎", "🍃", "🔥", "💡", "🐱", "✂️", "☀️", "🕶️"],
    ["⚡", "👋", "🐉", "🍾", "🌵", "✂️", "🔒", "🕸️"],
    ["⚓", "👋", "🧊", "❓", "🔨", "🐱", "🥕", "❄️"],
    ["❗", "🚙", "💡", "❤️", "🌵", "🌙", "❄️", "💀"],
]


class Colour(discord.Colour):
    @classmethod
    def dobble(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9A73A9``.

        .. colour:: #9A73A9

        .. versionadded:: 2.3
        """
        return cls(0x9A73A9)


class Game:
    def __init__(self, players: list[discord.Member], cards: list[list[str]], thread: discord.Thread):
        self.players = players
        self.cards = cards
        self.thread = thread

    async def add_player(self, player: discord.Member):
        self.players.append(player)
        await self.thread.add_user(player)

    @classmethod
    async def start(cls, interaction: I):
        cards = _cards.copy()
        random.shuffle(cards)
        thread = await interaction.channel.create_thread(name="Dobble")
        game = cls(
            players=[
                interaction.user,
            ],
            cards=cards,
            thread=thread,
        )

        join_game_view = JoinGameView(game)
        embed = discord.Embed(colour=Colour.dobble(), title="Dobble")
        await interaction.response.send_message(embed=embed, view=join_game_view)


class JoinGameView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=60)

        self.game = game

    @discord.ui.button(
        label="Join Game",
        style=discord.ButtonStyle.grey,
    )
    async def join_game(self, interaction: I, button: discord.ui.Button):
        await self.game.add_player(interaction.user)
        await interaction.response.defer()
