from typing import Optional, TypedDict, cast, TYPE_CHECKING, NotRequired
import discord
from redbot.core import commands
from redbot.core.bot import Red
import re

if TYPE_CHECKING:
    from .twitchnotifications import TwitchNotifications

I = discord.Interaction["Red"]


class PaginationData(TypedDict):
    cursor: NotRequired[str]


class StreamData(TypedDict):
    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str
    game_name: str
    type: str
    title: str
    tags: list[str]
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    is_mature: bool


class GetStreamsResponseData(TypedDict):
    data: list[StreamData]
    pagination: PaginationData


class TwitchUser(TypedDict):
    id: str
    login: str
    display_name: str
    type: str
    broadcaster_type: str
    description: str
    profile_image_url: str
    offline_image_url: str
    view_count: int
    email: str
    created_at: str


class TwitchUserTransformer(discord.app_commands.Transformer):
    @staticmethod
    def get_login_name(value: str) -> str:
        match = re.match(
            r"^(?:https?:\/\/)?(?:www\.)?twitch\.tv\/([a-zA-Z0-9_]+)$", value
        )
        if match:
            return match.group(1)

        if re.fullmatch(r"[a-zA-Z0-9_]+", value):
            return value
        raise ValueError("Invalid Twitch login name.")

    async def transform(self, interaction: I, value: str):  # type: ignore
        try:
            login_name = self.get_login_name(value)
        except ValueError as e:
            raise commands.UserInputError(message=str(e))

        cog = cast(
            "Optional[TwitchNotifications]",
            interaction.client.get_cog("TwitchNotifications"),
        )

        if not cog:
            raise commands.ExtensionNotLoaded("twitchnotifications")

        twitch_users = await cog.get_twitch_users(login_name)
        if not twitch_users:
            raise commands.UserInputError("No Twitch users found.")

        return twitch_users[0]


class TwitchUnauthorizedError(Exception):
    pass


class TwitchCredentialError(Exception):
    pass


class TwitchHTTPException(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)
