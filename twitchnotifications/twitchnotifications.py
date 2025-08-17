import logging
import re
import hmac
import hashlib
import secrets
from typing import TYPE_CHECKING, Optional, TypedDict, Annotated, cast
import aiohttp
import discord
from discord.utils import MISSING
from aiohttp import request, web
from aiohttp.web_runner import TCPSite
from multidict import MultiDict
from redbot.core import commands, app_commands, Config
import re
from typing import TYPE_CHECKING, Literal, Optional
import aiohttp
import discord
from discord.utils import MISSING
from aiohttp import web
from aiohttp.web_runner import TCPSite
from multidict import MultiDict
from redbot.core import commands, app_commands, Config
from .utils import (
    UserData,
    GetUsersResponseData,
    TwitchUserTransformer,
    TwitchUnauthorizedError,
    TwitchHTTPException,
    TwitchCredentialError,
    StreamData,
    PaginationData,
    GetStreamsResponseData,
)

if TYPE_CHECKING:
    from redbot.core.bot import Red

log = logging.getLogger("red.plumasium.twitchnotifications")
I = discord.Interaction["Red"]

TWITCH_API_BASE_URL = "https://api.twitch.tv/helix"
TWITCH_AUTH_BASE_URL = "https://id.twitch.tv/oauth2"


class TwitchNotifications(commands.Cog):
    def __init__(self, bot: "Red"):
        self.bot = bot
        self.config = Config.get_conf(cog_instance=self, identifier=722408471454023722)

        self.config.register_guild(subscribed_channels={})

        default_broadcaster = {"secret": "", "subscribed_guilds": []}
        self.config.init_custom("broadcaster", 1)
        self.config.register_custom("broadcaster", **default_broadcaster)

        self.web_server: TCPSite = MISSING

    async def cog_load(self):
        await self.setup_web_server()

    async def cog_unload(self):
        if not self.web_server is MISSING:
            await self.web_server.stop()

    twitch_notifications = app_commands.Group(
        name="twitch-notifications", description="Manage Twitch notifications."
    )

    @twitch_notifications.command(name="add")
    async def add_twitch_broadcaster(
        self,
        interaction: I,
        broadcaster_user: app_commands.Transform[UserData, TwitchUserTransformer],
    ):
        await interaction.response.send_message(broadcaster_user.get("id"))

    async def subscribe_to_broadcaster(self, broadcaster_user: UserData):
        broadcaster_subscription_secret = secrets.token_hex(32)
        await self.config.custom("broadcaster", broadcaster_user.get("id")).secret.set(
            broadcaster_subscription_secret
        )

        twitch_service = await self.bot.get_shared_api_tokens("twitch")
        client_id = twitch_service.get("client_id")
        access_token = twitch_service.get("access_token")
        default_callback = twitch_service.get("callback_url")

        if not client_id:
            raise TwitchCredentialError("Missing Twitch API client ID.")

        if not access_token:
            access_token = await self.get_new_twitch_access_token()

        callback_url = f"{default_callback}/twitchnotifications/stream/online"

        data = {
            "type": "stream.online",
            "version": "1",
            "condition": {"broadcaster_user_id": broadcaster_user.get("id")},
            "transport": {
                "method": "webhook",
                "callback": callback_url,
                "secret": broadcaster_subscription_secret,
            },
        }

        response_data = await self._twitch_api_request(
            client_id,
            access_token,
            "POST",
            "/eventsub/subscriptions",
            json=data,
        )
        log.info(f"Successfully subscribed: {response_data}")

    async def get_new_twitch_access_token(self):
        twitch_service = await self.bot.get_shared_api_tokens("twitch")

        client_id = twitch_service.get("client_id")
        client_secret = twitch_service.get("client_secret")

        if not client_id or not client_secret:
            raise TwitchCredentialError("Missing Twitch API credentials.")

        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{TWITCH_AUTH_BASE_URL}/token",
                params=params,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    await self.bot.set_shared_api_tokens(
                        "twitch",
                        access_token=data.get("access_token"),
                        expires_in=data.get("expires_in"),
                    )
                    return str(data.get("access_token"))

                else:
                    raise TwitchHTTPException(response.status, await response.text())

    async def get_streams(
        self,
        *,
        user_ids: tuple[str] | str = tuple(),
        user_logins: tuple[str] | str = tuple(),
        game_ids: tuple[str] | str = tuple(),
        stream_type: Optional[Literal["all", "live"]] = None,
        languages: tuple[str] | str = tuple(),
        first: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> GetStreamsResponseData:
        twitch_service = await self.bot.get_shared_api_tokens("twitch")
        client_id = twitch_service.get("client_id")
        access_token = twitch_service.get("access_token")

        if not client_id:
            raise TwitchCredentialError("Missing Twitch API client ID.")

        if not access_token:
            access_token = await self.get_new_twitch_access_token()

        params = MultiDict()

        if isinstance(user_ids, str):
            user_ids = (user_ids,)
        for user_id in user_ids:
            params.add("user_id", user_id)

        if isinstance(user_logins, str):
            user_logins = (user_logins,)
        for user_login in user_logins:
            params.add("user_login", user_login)

        if isinstance(game_ids, str):
            game_ids = (game_ids,)
        for game_id in game_ids:
            params.add("game_id", game_id)

        if stream_type:
            params.add("type", stream_type)

        if isinstance(languages, str):
            languages = (languages,)
        for language in languages:
            params.add("language", language)

        if first:
            params.add("first", first)

        if not before is None and not after is None:
            raise ValueError("Cannot specify both 'before' and 'after' parameters.")

        if before:
            params.add("before", before)
        if after:
            params.add("after", after)

        try:
            data: GetStreamsResponseData = await self._twitch_api_request(
                client_id,
                access_token,
                "GET",
                "/streams",
                params=params,
            )
            return data
        except TwitchUnauthorizedError as e:
            access_token = await self.get_new_twitch_access_token()
            data: GetStreamsResponseData = await self._twitch_api_request(
                client_id,
                access_token,
                "GET",
                "/streams",
                params=params,
            )
            return data

    async def get_twitch_users(self, *login_names: str) -> GetUsersResponseData:
        twitch_service = await self.bot.get_shared_api_tokens("twitch")
        client_id = twitch_service.get("client_id")
        access_token = twitch_service.get("access_token")

        if not client_id:
            raise TwitchCredentialError("Missing Twitch API client ID.")

        if not access_token:
            access_token = await self.get_new_twitch_access_token()

        params = MultiDict()
        for name in login_names:
            params.add("login", name)

        try:
            data: GetUsersResponseData = await self._twitch_api_request(
                client_id,
                access_token,
                "GET",
                "/users",
                params=params,
            )
            return data
        except TwitchUnauthorizedError as e:
            access_token = await self.get_new_twitch_access_token()
            data: GetUsersResponseData = await self._twitch_api_request(
                client_id,
                access_token,
                "GET",
                "/users",
                params=params,
            )
            return data

    async def _twitch_api_request(
        self,
        client_id: str,
        access_token: str,
        method: Literal["GET", "POST", "DELETE", "PATCH"],
        endpoint: str,
        **kwargs,
    ):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-Id": client_id,
        }

        url = f"{TWITCH_API_BASE_URL}{endpoint}"

        log.info(
            f"Making Twitch API request: {method} {url} with headers {headers} and params {kwargs}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                **kwargs,
            ) as response:
                if response.ok:
                    return await response.json()
                elif response.status == 401:
                    raise TwitchUnauthorizedError
                else:
                    raise TwitchHTTPException(response.status, await response.text())

    def create_twitch_signature(
        self, request: web.Request, secret: str, raw_body: bytes
    ) -> str:
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
            log.warning(
                "Missing required Twitch EventSub headers for signature verification"
            )
            return ""

        # Build the message for HMAC: message_id + timestamp + raw_body
        message = message_id + timestamp + raw_body.decode("utf-8")

        # Create HMAC-SHA256 signature
        expected_signature = (
            "sha256="
            + hmac.new(
                secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
            ).hexdigest()
        )

        return expected_signature

    def is_webhook_callback_verification_request(self, request: web.Request) -> bool:
        return (
            request.headers.get("twitch-eventsub-message-type")
            == "webhook_callback_verification"
        )

    def respond_to_webhook_callback_verification(self, data: dict) -> web.Response:
        challenge = data.get("challenge", "")

        headers = {"Content-Type": str(len(challenge))}
        return web.Response(status=200, text=challenge, headers=headers)

    async def stream_online_handler(self, request: web.Request) -> web.Response:
        data = await request.json()

        log.info(f"Received Twitch EventSub notification: {data}")

        if self.is_webhook_callback_verification_request(request):
            broadcaster_id = (
                data.get("subscription", {})
                .get("condition", {})
                .get("broadcaster_user_id")
            )
        else:
            broadcaster_id = data.get("event", {}).get("broadcaster_user_id")

        broadcaster_secret = await self.config.custom(
            "broadcaster", broadcaster_id
        ).secret()

        expected_signature = self.create_twitch_signature(
            request, broadcaster_secret, await request.read()
        )
        twitch_signature = request.headers.get("twitch-eventsub-message-signature", "")

        log.info(f"Expected Twitch signature: {expected_signature}")
        log.info(f"Received Twitch signature: {twitch_signature}")

        if not hmac.compare_digest(expected_signature, twitch_signature):
            log.warning("Twitch signature verification failed")
            return web.Response(status=403)

        if self.is_webhook_callback_verification_request(request):
            log.info(
                "Responding to webhook callback verification request with challenge"
            )
            return self.respond_to_webhook_callback_verification(data)

        guild = self.bot.get_guild(1379774648086036551)
        assert guild, "Guild not found"
        channel = guild.get_channel(1405956090591707176)
        assert isinstance(channel, discord.TextChannel), "Channel not found"

        data = await self.get_streams(user_ids=[data["event"]["broadcaster_user_id"]])  # type: ignore
        data = data.get("data", [])
        stream_data = data[0]

        await channel.send(f"Stream is now online!\n{stream_data}")

        return web.Response(status=200)

    async def test_handler(self, request: web.Request) -> web.Response:
        log.info("Test handler called successfully.")
        return web.Response(status=200, text="Test successful!")

    async def setup_web_server(self):
        app = web.Application()

        app.router.add_route(
            "POST", "/twitchnotifications/stream/online", self.stream_online_handler
        )

        app.router.add_route("POST", "/twitchnotifications/test", self.test_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        self.web_server = TCPSite(runner, port=8080)
        await self.web_server.start()
