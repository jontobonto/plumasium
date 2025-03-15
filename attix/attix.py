import discord
from discord.utils import MISSING
from redbot.core import commands, app_commands, Config
from typing import TYPE_CHECKING, Optional
import uuid

if TYPE_CHECKING:
    from redbot.core.bot import Red

import logging

I = discord.Interaction["Red"]

log = logging.getLogger("red.plumasium.attix")


class _View(discord.ui.View):
    def __init__(
        self,
        *,
        context: Optional[commands.Context] = None,
        interaction: Optional[discord.Interaction] = None,
        owner: Optional[discord.User] = None,
        owner_only: bool = True,
        timeout: Optional[float] = 300,
    ):
        super().__init__(timeout=timeout)
        self.context: Optional[commands.Context] = context
        self.interaction: Optional[I] = interaction or context.interaction
        self.owner: Optional[discord.User] = owner or (interaction.user if interaction else None)
        self.owner_only: bool = owner_only

        self.message: discord.Message = MISSING

        self._enabled: bool = self.interaction is not None

    async def on_timeout(self) -> None:
        if not self._enabled:
            return
        for item in self.children:
            if item.is_dispatchable():
                item.disabled = True

        if self.interaction:
            await self.interaction.edit_original_response(view=self)
        elif self.message:
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: I) -> bool:
        if self.owner_only and self.owner and interaction.user != self.owner:
            embed = discord.Embed(colour=discord.Color.red())
            embed.description = "Du bist nicht berechtigt, dieses Menü zu nutzen."
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True


class SelectQuestionView(discord.ui.View):
    def __init__(self, bot: "Red"):
        super().__init__(timeout=None)

        self.bot = bot


class Attix(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot = bot

        self.config = Config.get_conf(
            cog_instance=self,
            identifier=1349128827367985295,
            force_registration=True,
        )

        self.config.register_guild(questions=[])  # {"id": "", "question": "", "anwser": "", "letter": ""}
        self.config.register_member(solved_question_ids=[])

    _attix = app_commands.Group(
        name="attix",
        description="Verwalte das Quiz-System für Attix",
        guild_only=True,
        default_permissions=discord.Permissions(
            manage_guild=True,
        ),
    )

    @_attix.command(name="post")
    async def _attix_post(self, interaction: I, channel: discord.TextChannel):
        """Veröffentliche ein Quiz mit den aktuellen Fragen."""

    _attix_questions = app_commands.Group(name="questions", description="Verwalte die aktuellen Fragen", parent=_attix)

    @_attix_questions.command(name="add")
    async def _attix_questions_add(self, interaction: I, question: str, answer: str, letter: str):
        """Füge eine Frage hinzu."""
        _data = {"id": str(uuid.uuid4()), "question": question, "answer": answer, "letter": letter}

        async with self.config.guild(interaction.guild).questions() as questions:
            questions.append(_data)

        embed = discord.Embed()
        embed.color = discord.Color.green()
        embed.title = "Frage hinzugefügt"
        embed.description = f"> Frage: {question}\n> Antwort: {answer}\n> Lösungsbuchstabe: {letter}"
        embed.set_footer(text=_data["id"])

        await interaction.response.send_message(embed=embed)

    @_attix_questions.command(name="remove")
    async def _attix_questions_add(self, interaction: I, id: str):
        """Füge eine Frage hinzu."""
        questions: list[dict[str, str]] = await self.config.guild(interaction.guild).questions()

        found_question = next((q for q in questions if q["id"] == id), None)

        if found_question is None:
            embed = discord.Embed()
            embed.color = discord.Color.red()
            embed.title = "Frage nicht gefunden"
            embed.description = f"Es wurde keine Frage mit der ID `{id}` gefunden."

            await interaction.response.send_message(embed=embed)
            return

        questions.remove(found_question)
        await self.config.guild(interaction.guild).questions.set(questions)

        embed = discord.Embed()
        embed.color = discord.Color.green()
        embed.title = "Frage gelöscht"
        embed.description = f"> Frage: {found_question['question']}\n> Antwort: {found_question['answer']}\n> Lösungsbuchstabe: {found_question['letter']}"

        await interaction.response.send_message(embed=embed)
        return
    
