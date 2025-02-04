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


class GamePlayer(TypedDict):
    interaction: I
    game_message: discord.WebhookMessage
    cards: list[list[str]]


class Game:
    def __init__(self, max_players: int, players: dict[discord.Member, list[list[str]]], cards: list[list[str]], starting_interaction: I):
        self.max_players: int = max_players
        self.players: dict[discord.Member, GamePlayer] = players
        self.cards: list[list[str]] = cards
        self.starting_interaction: I = starting_interaction

        self.join_game_view: StartGameView = discord.utils.MISSING
        self.cards_views: list[CardsView] = discord.utils.MISSING

    @property
    def public_game_embed(self):
        embed = discord.Embed()
        embed.colour = Colour.dobble()
        embed.title = "Dobble!"

        _player_string = "\n".join([f"{len(m[1]['cards']) - 1} points - {m[0].mention}" for m in self.leaderboard])
        embed.description = f"👥 {len(self.players)}/{self.max_players} players\n{_player_string}"
        return embed

    @property
    def leaderboard(self):
        players = list(self.players.copy().items())
        return sorted(players, key=lambda p: len(p[1]["cards"]), reverse=True)

    @classmethod
    async def create(cls, interaction: I, max_players: int):
        cards = _cards.copy()
        for card in cards:
            random.shuffle(card)
        random.shuffle(cards)
        game = cls(
            max_players=max_players,
            players={},
            cards=cards,
            starting_interaction=interaction,
        )

        game.join_game_view = StartGameView(game)
        game.join_game_view._update()
        await interaction.response.send_message(embed=game.public_game_embed, view=game.join_game_view)

    async def add_player(self, player: discord.Member, join_interaction: I):
        if player in self.players.keys():
            raise IsAlreadyPlaying
        if len(self.players) >= self.max_players:
            raise GameFull
        self.players[player] = GamePlayer(interaction=join_interaction, cards=[])

        if self.starting_interaction.response.is_done():
            self.join_game_view._update()
            await self.starting_interaction.edit_original_response(embed=self.public_game_embed, view=self.join_game_view)

    async def start(self):
        for member, game_player in self.players.items():
            player_card = self.cards.pop(0)
            game_player["cards"].append(player_card)

        self.cards_views: list[CardsView] = []
        for member, game_player in self.players.items():
            view = CardsView(self, member, self.cards[0], game_player["cards"][-1])
            self.cards_views.append(view)
            game_player["game_message"] = await game_player["interaction"].followup.send(view=view, ephemeral=True, wait=True)

        await self.starting_interaction.edit_original_response(embed=self.public_game_embed, view=None)

    async def next_round(self, winner: discord.Member):
        winner_card = self.cards.pop(0)
        self.players[winner]["cards"].append(winner_card)

        if len(self.cards) == 0:
            for member, game_player in self.players.items():
                await game_player["game_message"].edit(content=f"🥇 {self.leaderboard[0][0].mention} has won!", view=None)

        else:
            self.cards_views: list[CardsView] = []
            for member, game_player in self.players.items():
                view = CardsView(self, member, self.cards[0], game_player["cards"][-1])
                self.cards_views.append(view)
                await game_player["game_message"].edit(view=view)

        await self.starting_interaction.edit_original_response(embed=self.public_game_embed)


class CardsView(discord.ui.View):
    def __init__(self, game: Game, player: discord.Member, card_1: list[str], card_2: list[str]):
        super().__init__(timeout=None)

        self.game = game
        self.player = player

        self.card_1 = card_1
        self.card_2 = card_2

        self.over = 0

        self._update()

    def _update(self):
        same_icon = (list(set(self.card_1) & set(self.card_2)))[0]

        for index, icon in enumerate(self.card_1):
            button = discord.ui.Button(style=discord.ButtonStyle.grey, emoji=icon, row=1 if index > 3 else 0)
            button.callback = self.correct_button if icon == same_icon else self.wrong_button
            self.add_item(button)

        button = discord.ui.Button(label=f"{len(self.game.players[self.player]['cards'])-1} points", style=discord.ButtonStyle.blurple, disabled=True, row=2)
        button.callback = self.wrong_button
        self.add_item(button)

        button = discord.ui.Button(label=f"{len(self.game.cards)} cards left", style=discord.ButtonStyle.blurple, disabled=True, row=2)
        button.callback = self.wrong_button
        self.add_item(button)
    

        for index, icon in enumerate(self.card_2):
            button = discord.ui.Button(style=discord.ButtonStyle.grey, emoji=icon, row=4 if index > 3 else 3)
            button.callback = self.correct_button if icon == same_icon else self.wrong_button
            self.add_item(button)

    async def wrong_button(self, interaction: I):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        self.game.players[interaction.user]["interaction"] = interaction

    async def correct_button(self, interaction: I):
        if self.over != 0:
            return await interaction.response.send_message(f"<@{self.over}> was faster than you...", ephemeral=True)
        await interaction.response.defer()
        
        for view in self.game.cards_views:
            view.over = interaction.user.id

        self.game.players[interaction.user]["interaction"] = interaction

        await self.game.next_round(interaction.user)


class StartGameView(discord.ui.View):
    def __init__(self, game: Game):
        super().__init__(timeout=None)

        self.game = game

    def _update(self):
        if len(self.game.players) >= self.game.max_players:
            self.join_game.disabled = True
        else:
            self.join_game.disabled = False

        if len(self.game.players) > 1:
            self.start_game.disabled = False
        else:
            self.start_game.disabled = True

    @discord.ui.button(
        label="Join Game",
        style=discord.ButtonStyle.grey,
    )
    async def join_game(self, interaction: I, button: discord.ui.Button):
        try:
            await self.game.add_player(interaction.user, interaction)
        except DobbleError as error:
            await interaction.response.send_message(error.message, ephemeral=True)
        else:
            await interaction.response.defer()

    @discord.ui.button(
        label="Start Game",
        style=discord.ButtonStyle.green,
    )
    async def start_game(self, interaction: I, button: discord.ui.Button):
        await interaction.response.defer()
        await self.game.start()


class DobbleError(Exception):
    def __init__(self, message: Optional[str] = None, *args):
        self.message = message
        super().__init__(*args)


class IsAlreadyPlaying(DobbleError):
    def __init__(self) -> None:
        super().__init__("❌ You're already a player in this game.")


class GameFull(DobbleError):
    def __init__(self) -> None:
        super().__init__("❌ This game is currently full.")
