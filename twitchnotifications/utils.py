import hashlib
import hmac
import logging
import re
from typing import TYPE_CHECKING, NotRequired, Optional, TypedDict, cast

import discord
from aiohttp import web
from discord.types.embed import Embed as DiscordEmbed
from discord.types.embed import EmbedAuthor as DiscordEmbedAuthor
from discord.types.embed import EmbedField as DiscordEmbedField
from discord.types.embed import EmbedFooter as DiscordEmbedFooter
from discord.types.embed import EmbedMedia as DiscordEmbedMedia
from discord.types.embed import EmbedProvider as DiscordEmbedProvider
from redbot.core import commands
from redbot.core.bot import Red

log = logging.getLogger("red.plumasium.twitchnotifications")

if TYPE_CHECKING:
    from .twitchnotifications import TwitchNotifications

I = discord.Interaction["Red"]


class DiscordNotificationMessage(TypedDict, total=False):
    content: str
    embed: DiscordEmbed


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


class UserData(TypedDict):
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


class GetUsersResponseData(TypedDict):
    data: list[UserData]


def replace_variables_in_notification(
    message_data: DiscordNotificationMessage, stream_data: Optional[StreamData], user_data: Optional[UserData]
) -> DiscordNotificationMessage:
    """
    Recursively replace all variables in a DiscordNotificationMessage
    with values from stream_data and user_data.

    Format: $user.var_name for user data, $stream.var_name for stream data

    #### User Data Variables (from UserData):
    $user.id - User ID
    $user.login - Username (login name)
    $user.display_name - Display name
    $user.type - User type
    $user.broadcaster_type - Broadcaster type
    $user.description - User description
    $user.profile_image_url - Profile image URL
    $user.offline_image_url - Offline image URL
    $user.view_count - View count
    $user.email - Email
    $user.created_at - Account creation date
    #### Stream Data Variables (from StreamData):
    $stream.id - Stream ID
    $stream.user_id - User ID
    $stream.user_login - Username
    $stream.user_name - User display name
    $stream.game_id - Game ID
    $stream.game_name - Game name
    $stream.type - Stream type
    $stream.title - Stream title
    $stream.tags - Stream tags
    $stream.viewer_count - Current viewer count
    $stream.started_at - Stream start time
    $stream.language - Stream language
    $stream.thumbnail_url - Raw thumbnail URL
    $stream.is_mature - Mature content flag
    #### Special Variables:
    $stream_url - Constructed URL: https://twitch.tv/{login}
    $stream.thumbnail_url_hd - HD thumbnail (1920x1080)
    """

    def replace_in_value(value):
        if isinstance(value, str):
            # Replace $user.var_name variables
            if user_data:
                for key, val in user_data.items():
                    variable = f"$user.{key}"
                    if variable in value:
                        if isinstance(val, str):
                            value = value.replace(variable, val)
                        else:
                            value = value.replace(variable, str(val))

            # Replace $stream.var_name variables
            if stream_data:
                for key, val in stream_data.items():
                    variable = f"$stream.{key}"
                    if variable in value:
                        if isinstance(val, str):
                            value = value.replace(variable, val)
                        else:
                            value = value.replace(variable, str(val))

            # Special constructed variables
            if stream_data:
                # Stream URL: https://twitch.tv/username
                value = value.replace("$stream.url", f"https://twitch.tv/{stream_data.get('user_login', '')}")

            if stream_data:
                # Thumbnail URL with proper dimensions
                thumbnail = stream_data.get("thumbnail_url", "")
                if thumbnail:
                    thumbnail = thumbnail.replace("{width}", "1920").replace("{height}", "1080")
                value = value.replace("$stream.thumbnail_url_hd", thumbnail)

            return value
        elif isinstance(value, dict):
            return {k: replace_in_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [replace_in_value(item) for item in value]
        else:
            return value

    return cast(DiscordNotificationMessage, replace_in_value(message_data))


def is_webhook_callback_verification_request(request: web.Request) -> bool:
    return request.headers.get("twitch-eventsub-message-type") == "webhook_callback_verification"


def respond_to_webhook_callback_verification(data: dict) -> web.Response:
    challenge = data.get("challenge", "")

    headers = {"Content-Type": str(len(challenge))}
    return web.Response(status=200, text=challenge, headers=headers)


def create_twitch_signature(request: web.Request, secret: str, raw_body: bytes) -> str:
    """
    Verify that a webhook request came from Twitch by validating the HMAC signature.

    Args:
        request: The aiohttp request object
        secret: The secret key used when creating the subscription
        raw_body: The raw request body as bytes

    Returns:
        True if the signature is valid, False otherwise

    Implementation based on:
    https://dev.twitch.tv/docs/eventsub/handling-webhook-events/#verifying-the-event-message
    """
    # Get required headers
    message_id = request.headers.get("twitch-eventsub-message-id")
    timestamp = request.headers.get("twitch-eventsub-message-timestamp")

    if not message_id or not timestamp:
        log.warning("Missing required Twitch EventSub headers for signature verification")
        return ""

    # Build the message for HMAC: message_id + timestamp + raw_body
    message = message_id + timestamp + raw_body.decode("utf-8")

    # Create HMAC-SHA256 signature
    expected_signature = (
        "sha256=" + hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    )

    return expected_signature


class TwitchUserTransformer(discord.app_commands.Transformer):
    @staticmethod
    def get_login_name(value: str) -> str:
        match = re.match(r"^(?:https?:\/\/)?(?:www\.)?twitch\.tv\/([a-zA-Z0-9_]+)$", value)
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

        user_data = twitch_users.get("data", [])
        return user_data[0]


class TwitchUnauthorizedError(Exception):
    pass


class TwitchCredentialError(Exception):
    pass


class TwitchHTTPException(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)
