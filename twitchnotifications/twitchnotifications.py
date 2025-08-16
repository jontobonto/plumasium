import logging
import re
from typing import TYPE_CHECKING, Literal, Optional, TypedDict, Annotated, cast
import aiohttp
import discord
from discord.utils import MISSING
from aiohttp import web
from aiohttp.web_runner import TCPSite
from multidict import MultiDict
from redbot.core import commands, app_commands, Config

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

        self.web_server: TCPSite = MISSING

    async def cog_load(self):
        return
        await self.setup_web_server()

    async def cog_unload(self):
        return
        await self.web_server.stop()

    twitch_notifications = app_commands.Group(
        name="twitch-notifications", description="Manage Twitch notifications."
    )

    @twitch_notifications.command(name="add")
    async def add_twitch_channel(self, interaction: I, channel: discord.TextChannel):
        await interaction.response.send_message(
            f"Added {channel.mention} to the Twitch channel list."
        )

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
                        {
                            "twitch": {
                                "access_token": data.get("access_token"),
                                "expires_in": data.get("expires_in"),
                            }
                        }
                    )
                    return str(data.get("access_token"))

                else:
                    raise TwitchHTTPException(response.status, await response.text())

    async def get_twitch_users(self, *login_names: str) -> list["TwitchUser"]:
        twitch_service = await self.bot.get_shared_api_tokens("twitch")
        client_id = twitch_service.get("client_id")
        access_token = twitch_service.get("access_token")

        if not access_token:
            access_token = await self.get_new_twitch_access_token()

        params = MultiDict()
        for name in login_names:
            params.add("login", name)

        try:
            data = await self._twitch_api_request(
                client_id,
                access_token,
                "GET",
                "/users",
                params=params,
            )
            return data.get("data", [])
        except TwitchUnauthorizedError as e:
            access_token = await self.get_new_twitch_access_token()
            data = await self._twitch_api_request(
                client_id,
                access_token,
                "GET",
                "/users",
                params=params,
            )
            return data.get("data", [])

    async def _twitch_api_request(
        self,
        client_id: str,
        access_token: str,
        method: Literal["GET", "POST", "DELETE", "PATCH"],
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-Id": client_id,
        }

        url = f"{TWITCH_API_BASE_URL}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
                data=data,
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise TwitchUnauthorizedError
                else:
                    raise TwitchHTTPException(response.status, await response.text())

    async def setup_web_server(self):
        app = web.Application()
        # /cases/{guild_id}/{user_id}
        app.router.add_route(
            "POST", "/twitch/notifications", self.notifications_handler
        )

        runner = web.AppRunner(app)
        await runner.setup()
        self.web_server = TCPSite(runner, port=8080)
        await self.web_server.start()


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

    async def transform(self, interaction: I, value: str) -> discord.Message:
        try:
            login_name = self.get_login_name(value)
        except ValueError as e:
            raise commands.UserInputError(message=str(e))

        cog = cast(
            "Optional[TwitchNotifications]",
            interaction.client.get_cog("TwitchNotifications"),
        )

        twitch_users = await cog.get_twitch_users(login_name)


class TwitchUnauthorizedError(Exception):
    pass


class TwitchCredentialError(Exception):
    pass


class TwitchHTTPException(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)
