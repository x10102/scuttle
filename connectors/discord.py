# Builtins
import json
import time
import typing as t
from logging import warning, error, info
from flask import current_app
from http import HTTPStatus

# External
import requests

API_UA = "SCUTTLE Discord service (https://scp-wiki.cz, v1)"
API_URL = "https://discord.com/api/v10"
CDN_URL = "https://cdn.discordapp.com"

RATELIMIT_RETRIES = 3

class DiscordWebhookMessage():
    text_content: str
    pings: t.List[int]

    def _build_text_content(self) -> str:
        content = ""
        for p in self.pings:
            content += f"<@{p}> "
        content += self.text_content
        return content

    def add_ping(self, user_id: int):
        self.pings.append(user_id)

    def to_json(self) -> dict:
        return {"content": self._build_text_content()}

class DiscordWebhookException(RuntimeError):
    pass

class DiscordException(Exception):
    pass

class DiscordClient():

    def __new__(*args, **kwargs):
        # Pretend python has static classes and this is one
        raise TypeError("Static class cannot be instantiated")

    @staticmethod
    def init_app(app):
        auth_token = app.config.get('DISCORD_TOKEN', "")
        DiscordClient.__auth_token = auth_token
        DiscordClient.__request_headers = {
            "User-Agent": API_UA,
            "Authorization": f"Bot {DiscordClient.__auth_token}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _validate_user_id(uid: str):
        if len(uid) not in [18, 19]:
            return False
        try:
            _ = int(uid)
        except Exception:
            return False
        return True
    
    @staticmethod
    def _get_user(uid: int) -> t.Optional[dict]:
        
        retry = 0
        while retry < RATELIMIT_RETRIES:
            response = requests.get(API_URL + f'/users/{uid}', headers=DiscordClient.__request_headers)
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                wait_sec = 2**retry
                warning(f"Rate limited! Waiting for {wait_sec}")
                time.sleep(wait_sec)
                retry += 1
            else:
                break

        if response.status_code == HTTPStatus.OK:
            return json.loads(response.content)
        elif response.status_code == HTTPStatus.NOT_FOUND:
            warning(f'Discord user API returned 404 for {uid}')
            return None
        else:
            error(f'Discord API request failed for {uid}')
            raise DiscordException("API Request failed")

    @staticmethod
    def get_global_username(uid: int) -> t.Optional[str]:
        """
        Fetches the global nickname, if the user doesn't have any set, returns the username

        :param int uid: The user's Discord ID
        :raises DiscordException: When either of the API requests fails
        :return: The nickname / username. None is returned if the request succeeds but some other unexpected error occurs
        :rtype: Optional[str]
        """
        
        try:
            user = DiscordClient._get_user(uid)
        except DiscordException as e:
            raise e
        if user is None:
            return None
        if user['global_name'] == None:
            return user['username']
        return user['global_name']

    @staticmethod
    def get_avatar(uid: int, size = 256) -> bytes:
        """
        Fetches the avatar of a user from Discord's CDN. Results are cached for 6 hours.

        :param int uid: The user's Discord ID
        :param int size: The avatar's size, defaults to 512 px
        :raises DiscordException: When either of the API requests fails
        :return: The user's avatar in PNG format
        :rtype: bytes
        """
        try:
            user = DiscordClient._get_user(uid)
        except DiscordException as e:
            raise e

        if user is None:
            return None

        endpoint = CDN_URL + f"/avatars/{uid}/{user['avatar']}.png"
        
        retry = 0
        while retry < RATELIMIT_RETRIES:
            response = requests.get(endpoint, headers=DiscordClient.__request_headers, params={'size': str(size)})
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                wait_sec = 2**retry
                warning(f"Rate limited! Waiting for {wait_sec}")
                time.sleep(wait_sec)
                retry += 1
            else:
                break

        if response.status_code == HTTPStatus.OK:
            return response.content
        elif response.status_code == HTTPStatus.NOT_FOUND:
            warning(f"Discord CDN request returned 404 for {uid}")
            return None
        else:
            error(f"Discord CDN request failed for {uid}")
            raise DiscordException("CDN Request failed")

class DiscordWebhook():
    """
    Utility class for sending webhooks
    """
    def __init__(self, url: str = None, notify = 0) -> None:
        self.url = url
        self.notify = notify

    
    def init_app(self, app):
        self.url = app.config['DISCORD_WEBHOOK_URL']
        self.notify = app.config['DISCORD_ROLEMASTER_ID']

    def send_text(self, message: str, ping_user: int = 0) -> None:
        if not self.url:
            raise DiscordWebhookException('Cannot send an uninitialized webhook (no URL specified)')
        if current_app.config['DEBUG'] == True:
            message = f"[TESTOVACÍ REŽIM - PROSÍM IGNORUJTE] {message}"
        if len(message) > 2000:
            raise ValueError(f'Message is too long ({len(message)} characters)')
        if ping_user:
            data = {"content": f'<@{ping_user}> {message}'}
        elif self.notify:
            data = {"content": f'<@{self.notify}> {message}'}
        else:
            data = {"content": message}
        info('Sending webhook')
        try:
            webhook_response = requests.post(self.url, json=data)
        except Exception as e:
            error(f'Webhook failed to send ({str(e)})')

    def _send_json(self, data: dict):
        if not self.url:
            raise DiscordWebhookException('Cannot send an uninitialized webhook (no URL specified)')
        info("Sending JSON webhook")
        try:
            webhook_response = requests.post(self.url, json=data)
        except Exception as e:
            error(f'Webhook failed to send ({str(e)})')