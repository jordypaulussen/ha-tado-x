"""API client for Tado X."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
import ssl

from .const import (
    TADO_AUTH_URL,
    TADO_CLIENT_ID,
    TADO_EIQ_API_URL,
    TADO_HOPS_API_URL,
    TADO_MINDER_API_URL,
    TADO_MY_API_URL,
    TADO_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


class TadoXAuthError(Exception):
    """Exception for authentication errors."""


class TadoXApiError(Exception):
    """Exception for API errors."""


class TadoXRateLimitError(TadoXApiError):
    """Exception for rate limit (429) errors."""

    def __init__(self, message: str, reset_time: datetime | None = None):
        super().__init__(message)
        self.reset_time = reset_time


class TadoXApi:
    """Tado X API client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_expiry: datetime | None = None,
        api_calls_today: int = 0,
        api_reset_time: datetime | None = None,
        has_auto_assist: bool = False,
        on_token_refresh: callable | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expiry = token_expiry
        self._home_id: int | None = None
        self._has_auto_assist = has_auto_assist
        self._on_token_refresh = on_token_refresh

        now = datetime.now(timezone.utc)
        default_reset_time = self._calculate_next_reset_time(now)

        if api_reset_time and api_reset_time > now:
            self._api_calls_today = api_calls_today
            self._api_call_reset_time = api_reset_time
        else:
            self._api_calls_today = 0
            self._api_call_reset_time = default_reset_time

        self._api_quota_limit: int | None = None
        self._api_quota_remaining: int | None = None

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    @property
    def token_expiry(self) -> datetime | None:
        return self._token_expiry

    @property
    def home_id(self) -> int | None:
        return self._home_id

    @home_id.setter
    def home_id(self, value: int) -> None:
        self._home_id = value

    @property
    def api_calls_today(self) -> int:
        return self._api_calls_today

    @property
    def api_reset_time(self) -> datetime:
        return self._api_call_reset_time

    @property
    def has_auto_assist(self) -> bool:
        return self._has_auto_assist

    @has_auto_assist.setter
    def has_auto_assist(self, value: bool) -> None:
        self._has_auto_assist = value

    @property
    def api_quota_limit(self) -> int | None:
        return self._api_quota_limit

    @property
    def api_quota_remaining(self) -> int | None:
        return self._api_quota_remaining

    @staticmethod
    def _calculate_next_reset_time(now: datetime) -> datetime:
        reset_hour = 12
        today_reset = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
        return today_reset + timedelta(days=1) if now >= today_reset else today_reset

    def _parse_rate_limit_headers(self, headers: dict) -> None:
        import re
        policy_header = headers.get("ratelimit-policy", "")
        if policy_header:
            quota_match = re.search(r"q=(\d+)", policy_header)
            if quota_match:
                self._api_quota_limit = int(quota_match.group(1))
        ratelimit_header = headers.get("ratelimit", "")
        if ratelimit_header:
            remaining_match = re.search(r"r=(\d+)", ratelimit_header)
            if remaining_match:
                self._api_quota_remaining = int(remaining_match.group(1))

    async def start_device_auth(self) -> dict[str, Any]:
        _LOGGER.warning("Starting device authorization flow")
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        ssl_context = ssl.create_default_context()
        connector = aiohttp.TCPConnector(force_close=True, ssl=ssl_context)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as auth_session:
            try:
                _LOGGER.warning("Sending request to %s", TADO_AUTH_URL)
                async with auth_session.post(
                    TADO_AUTH_URL,
                    data={"client_id": TADO_CLIENT_ID, "scope": "offline_access"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    _LOGGER.warning("Device auth response status: %s", response.status)
                    if response.status != 200:
                        text = await response.text()
                        _LOGGER.error("Failed to start device auth: %s - %s", response.status, text)
                        raise TadoXAuthError(f"Failed to start device auth: {response.status}")
                    result = await response.json()
                    _LOGGER.warning("Device auth successful, got user_code: %s", result.get("user_code"))
                    return result
            except asyncio.TimeoutError as err:
                raise TadoXAuthError("Timeout during device auth request") from err
            except aiohttp.ClientError as err:
                raise TadoXAuthError(f"Network error: {err}") from err
            except ssl.SSLError as err:
                raise TadoXAuthError(f"SSL error: {err}") from err
            except Exception as err:
                raise TadoXAuthError(f"Unexpected error: {err}") from err

    async def poll_for_token(self, device_code: str, interval: int = 5, timeout: int = 300) -> bool:
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < timeout:
            try:
                async with self._session.post(
                    TADO_TOKEN_URL,
                    data={
                        "client_id": TADO_CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    data = await response.json()
                    if response.status == 200:
                        self._access_token = data["access_token"]
                        self._refresh_token = data.get("refresh_token")
                        expires_in = data.get("expires_in", 600)
                        self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
                        return True
                    if data.get("error") == "authorization_pending":
                        await asyncio.sleep(interval)
                        continue
                    raise TadoXAuthError(f"Token error: {data.get('error_description', data.get('error'))}")
            except aiohttp.ClientError as err:
                await asyncio.sleep(interval)
        return False

    async def refresh_access_token(self) -> bool:
        if not self._refresh_token:
            raise TadoXAuthError("No refresh token available")
        try:
            async with self._session.post(
                TADO_TOKEN_URL,
                data={"client_id": TADO_CLIENT_ID, "grant_type": "refresh_token", "refresh_token": self._refresh_token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise TadoXAuthError(f"Failed to refresh token: {response.status} - {text}")
                data = await response.json()
                self._access_token = data["access_token"]
                self._refresh_token = data.get("refresh_token", self._refresh_token)
                expires_in = data.get("expires_in", 600)
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
                if self._on_token_refresh:
                    self._on_token_refresh()
                return True
        except aiohttp.ClientError as err:
            raise TadoXAuthError(f"Network error during token refresh: {err}") from err

    async def _ensure_valid_token(self) -> None:
        if not self._access_token:
            raise TadoXAuthError("Not authenticated")
        if self._token_expiry and datetime.now() >= self._token_expiry - timedelta(seconds=60):
            await self.refresh_access_token()

    async def _request(self, method: str, url: str, json_data: dict | None = None) -> dict | list | None:
        await self._ensure_valid_token()
        self._api_calls_today += 1
        now = datetime.now(timezone.utc)
        if now >= self._api_call_reset_time:
            self._api_calls_today = 1
            self._api_call_reset_time = self._calculate_next_reset_time(now)
        headers = {"Authorization": f"Bearer {self._access_token}", "Content-Type": "application/json"}

        try:
            async with self._session.request(method, url, headers=headers, json=json_data) as response:
                self._parse_rate_limit_headers(response.headers)
                if response.status == 401:
                    await self.refresh_access_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.request(method, url, headers=headers, json=json_data) as retry_response:
                        if retry_response.status != 200:
                            text = await retry_response.text()
                            raise TadoXApiError(f"API error: {retry_response.status} - {text}")
                        return await retry_response.json() if retry_response.content_length != 0 else None
                if response.status == 429:
                    raise TadoXRateLimitError("API rate limit exceeded", reset_time=self._api_call_reset_time)
                if response.status not in (200, 204):
                    text = await response.text()
                    raise TadoXApiError(f"API error: {response.status} - {text}")
                return await response.json() if response.content_length != 0 else None
        except aiohttp.ClientError as err:
            raise TadoXApiError(f"Network error: {err}") from err

    # ---------------- My Tado endpoints ----------------
    async def get_me(self) -> dict[str, Any]:
        result = await self._request("GET", f"{TADO_MY_API_URL}/me")
        return result if isinstance(result, dict) else {}

    async def get_homes(self) -> list[dict[str, Any]]:
        me = await self.get_me()
        return me.get("homes", [])

    async def get_home_state(self) -> dict[str, Any]:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        result = await self._request("GET", f"{TADO_MY_API_URL}/homes/{self._home_id}/state")
        return result if isinstance(result, dict) else {}

    async def set_presence_home(self) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        await self._request("PUT", f"{TADO_MY_API_URL}/homes/{self._home_id}/presenceLock", json_data={"homePresence": "HOME"})

    async def set_presence_away(self) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        await self._request("PUT", f"{TADO_MY_API_URL}/homes/{self._home_id}/presenceLock", json_data={"homePresence": "AWAY"})

    async def set_presence_auto(self) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        await self._request("DELETE", f"{TADO_MY_API_URL}/homes/{self._home_id}/presenceLock")

    async def get_mobile_devices(self) -> list[dict[str, Any]]:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        result = await self._request("GET", f"{TADO_MY_API_URL}/homes/{self._home_id}/mobileDevices")
        return result if isinstance(result, list) else []

    async def get_weather(self) -> dict[str, Any]:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        result = await self._request("GET", f"{TADO_MY_API_URL}/homes/{self._home_id}/weather")
        return result if isinstance(result, dict) else {}

    # ---------------- Hops / Tado X endpoints ----------------
    async def get_rooms(self) -> list[dict[str, Any]]:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        result = await self._request("GET", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/rooms")
        return result if isinstance(result, list) else []

    async def get_rooms_and_devices(self) -> dict[str, Any]:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        result = await self._request("GET", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/roomsAndDevices")
        return result if isinstance(result, dict) else {}

    async def set_room_temperature(self, room_id: int, temperature: float, power: str = "ON", termination_type: str = "TIMER", duration_seconds: int = 1800) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        data: dict[str, Any] = {
            "setting": {"power": power, "temperature": {"value": temperature}},
            "termination": {"type": termination_type},
        }
        if termination_type == "TIMER":
            data["termination"]["durationInSeconds"] = duration_seconds
        await self._request("POST", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/rooms/{room_id}/manualControl", json_data=data)

    async def set_room_off(self, room_id: int, termination_type: str = "TIMER", duration_seconds: int = 1800) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        data: dict[str, Any] = {"setting": {"power": "OFF"}, "termination": {"type": termination_type}}
        if termination_type == "TIMER":
            data["termination"]["durationInSeconds"] = duration_seconds
        await self._request("POST", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/rooms/{room_id}/manualControl", json_data=data)

    async def resume_schedule(self, room_id: int) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        await self._request("DELETE", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/rooms/{room_id}/manualControl")

    async def boost_all_heating(self) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        await self._request("POST", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/quickActions/boost")

    async def disable_all_heating(self) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        await self._request("POST", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/quickActions/allOff")

    async def resume_all_schedules(self) -> None:
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        await self._request("POST", f"{TADO_HOPS_API_URL}/homes/{self._home_id}/quickActions/resumeSchedule")

    # ---------------- Boiler / Water Heater ----------------
    async def set_boiler_temperature(self, serial_number: str, temperature: float) -> None:
        """Set the target temperature for a boiler device (°C)."""
        if not self._home_id:
            raise TadoXApiError("Home ID not set")
        payload = {"temperature": {"celsius": temperature}, "power": "ON"}
        url = f"{TADO_HOPS_API_URL}/homes/{self._home_id}/devices/{serial_number}/state"
        _LOGGER.debug("Setting boiler %s temperature to %.1f°C with payload: %s", serial_number, temperature, payload)
        result = await self._request("PUT", url, json_data=payload)
        _LOGGER.info("Boiler %s temperature set to %.1f°C, response: %s", serial_number, temperature, result)
