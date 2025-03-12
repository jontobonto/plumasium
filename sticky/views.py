from typing import Optional

import discord
from discord import Interaction
from discord._types import ClientT
from fndeutils import Modal


class StickySetModal(Modal, title='Set Sticky Message'):
    text_input = discord.ui.TextInput(label='Text', style=discord.TextStyle.long)

    def __init__(self, text: Optional[str]):
        super().__init__()
        self.interaction: Optional[Interaction[ClientT]] = None
        if text:
            self.text_input.default = text

    async def on_submit(self, interaction: Interaction[ClientT], /) -> None:
        self.interaction = interaction


class StickyButtonModal(Modal, title='Configure Sticky Button'):
    label_input = discord.ui.TextInput(label='Label', max_length=80)
    value_input = discord.ui.TextInput(label='', max_length=100)

    def __init__(self, type_: int):
        super().__init__()
        self.interaction: Optional[Interaction[ClientT]] = None
        if type_ == 0:
            self.value_input.label = 'URL'
        elif type_ == 1:
            self.value_input.label = 'Custom ID'

    async def on_submit(self, interaction: Interaction[ClientT], /) -> None:
        self.interaction = interaction
