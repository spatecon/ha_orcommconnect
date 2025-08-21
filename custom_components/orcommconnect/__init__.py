"""Orcomm Connect integration for Home Assistant."""
import asyncio
import logging
from datetime import timedelta

import aiohttp
import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.SWITCH, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Orcomm Connect from a config entry."""
    
    session = async_get_clientsession(hass)
    api = OrcommConnectAPI(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    # Test connection
    try:
        devices = await api.async_get_devices()
    except Exception as err:
        _LOGGER.error("Failed to connect to Orcomm Connect: %s", err)
        raise ConfigEntryNotReady from err

    scan_interval = timedelta(
        seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    coordinator = OrcommConnectDataUpdateCoordinator(hass, api, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "devices": devices,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class OrcommConnectAPI:
    """API client for Orcomm Connect."""

    def __init__(self, host: str, username: str, password: str, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self.host = host
        self.username = username
        self.password = password
        self.session = session
        self.base_url = f"http://{host}:1443"

    async def async_get_devices(self) -> list[dict]:
        """Get all devices from the Orcomm Connect system."""
        url = f"{self.base_url}/devices"
        auth = aiohttp.BasicAuth(self.username, self.password)
        
        try:
            async with async_timeout.timeout(10):
                async with self.session.get(url, auth=auth) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("devices", [])
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout communicating with Orcomm Connect") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Orcomm Connect: {err}") from err

    async def async_switch_device(self, device_uid: str, power_state: bool, brightness: int = None) -> bool:
        """Switch a device on or off with optional brightness."""
        url = f"{self.base_url}/device/switch"
        auth = aiohttp.BasicAuth(self.username, self.password)
        
        payload = {
            "switches": [
                {
                    "device_uid": device_uid,
                    "power_state": power_state,
                }
            ]
        }
        
        if brightness is not None:
            payload["switches"][0]["brightness"] = brightness

        try:
            async with async_timeout.timeout(10):
                async with self.session.post(url, json=payload, auth=auth) as response:
                    response.raise_for_status()
                    return True
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout communicating with Orcomm Connect") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Orcomm Connect: {err}") from err

    async def async_locate_device(self, address: int, channel: int = 0, state: bool = True) -> bool:
        """Locate a device by making it blink."""
        url = f"{self.base_url}/device/locate"
        auth = aiohttp.BasicAuth(self.username, self.password)
        
        payload = {
            "address": address,
            "channel": channel,
            "state": state,
        }

        try:
            async with async_timeout.timeout(10):
                async with self.session.post(url, json=payload, auth=auth) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("success", False)
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout communicating with Orcomm Connect") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Orcomm Connect: {err}") from err


class OrcommConnectDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Orcomm Connect."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: OrcommConnectAPI,
        scan_interval: timedelta,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )
        self.api = api

    async def _async_update_data(self) -> list[dict]:
        """Update data via library."""
        try:
            return await self.api.async_get_devices()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err