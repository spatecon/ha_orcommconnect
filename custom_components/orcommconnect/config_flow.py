"""Config flow for Orcomm Connect integration."""
import asyncio
import ipaddress
import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_PASSWORD, DEFAULT_USERNAME

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
    }
)

STEP_DISCOVERY_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("subnet", default="192.168.1.0/24"): str,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    session = async_get_clientsession(hass)
    host = data[CONF_HOST]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    
    url = f"http://{host}:1443/devices"
    auth = aiohttp.BasicAuth(username, password)
    
    try:
        async with async_timeout.timeout(10):
            async with session.get(url, auth=auth) as response:
                if response.status == 401:
                    raise InvalidAuth
                response.raise_for_status()
                devices_data = await response.json()
                devices = devices_data.get("devices", [])
                
    except aiohttp.ClientError as err:
        _LOGGER.error("Error connecting to Orcomm Connect: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error: %s", err)
        raise CannotConnect from err

    return {
        "title": f"Orcomm Connect ({host})",
        "devices_count": len(devices),
    }


async def discover_orcomm_devices(hass: HomeAssistant, subnet: str, username: str, password: str) -> list[dict[str, Any]]:
    """Discover Orcomm Connect devices on the network."""
    session = async_get_clientsession(hass)
    auth = aiohttp.BasicAuth(username, password)
    discovered_devices = []
    
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError as err:
        _LOGGER.error("Invalid subnet format: %s", err)
        raise InvalidSubnet from err
    
    # Limit scan to reasonable subnet sizes to avoid overwhelming the network
    if network.num_addresses > 1024:
        raise SubnetTooLarge
    
    async def check_host(ip: str) -> dict[str, Any] | None:
        """Check if a host has an Orcomm Connect device."""
        url = f"http://{ip}:1443/"
        try:
            async with async_timeout.timeout(3):
                async with session.get(url, auth=auth) as response:
                    # Based on RND data, we expect a 404 with "This URI does not exist" for root path
                    if response.status == 404:
                        text = await response.text()
                        if "This URI does not exist" in text:
                            # This looks like an Orcomm device, now check /devices endpoint
                            devices_url = f"http://{ip}:1443/devices"
                            try:
                                async with async_timeout.timeout(5):
                                    async with session.get(devices_url, auth=auth) as devices_response:
                                        if devices_response.status == 200:
                                            devices_data = await devices_response.json()
                                            devices = devices_data.get("devices", [])
                                            return {
                                                "host": ip,
                                                "devices_count": len(devices),
                                                "status": "authenticated"
                                            }
                                        elif devices_response.status == 401:
                                            return {
                                                "host": ip,
                                                "devices_count": 0,
                                                "status": "auth_required"
                                            }
                            except (asyncio.TimeoutError, aiohttp.ClientError):
                                pass
        except (asyncio.TimeoutError, aiohttp.ClientError):
            pass
        return None
    
    # Create tasks for all IP addresses in the subnet
    tasks = []
    for ip in network.hosts():
        # Skip broadcast and network addresses for smaller subnets
        if network.prefixlen >= 24:  # /24 or smaller
            tasks.append(check_host(str(ip)))
        else:
            # For larger subnets, only check every 4th address to reduce load
            if int(ip) % 4 == 0:
                tasks.append(check_host(str(ip)))
    
    # Execute discovery with controlled concurrency
    semaphore = asyncio.Semaphore(20)  # Limit to 20 concurrent requests
    
    async def bounded_check(task):
        async with semaphore:
            return await task
    
    _LOGGER.info("Scanning %d IP addresses for Orcomm Connect devices", len(tasks))
    results = await asyncio.gather(*[bounded_check(task) for task in tasks], return_exceptions=True)
    
    for result in results:
        if isinstance(result, dict) and result is not None:
            discovered_devices.append(result)
    
    _LOGGER.info("Discovery completed, found %d potential Orcomm Connect devices", len(discovered_devices))
    return discovered_devices


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Orcomm Connect."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices: list[dict[str, Any]] = []
        self._selected_host: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - choice between manual and discovery."""
        if user_input is not None:
            if user_input["setup_mode"] == "manual":
                return await self.async_step_manual()
            elif user_input["setup_mode"] == "discovery":
                return await self.async_step_discovery()

        data_schema = vol.Schema(
            {
                vol.Required("setup_mode", default="manual"): vol.In({
                    "manual": "Manual IP Entry",
                    "discovery": "Automatic Discovery"
                })
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual IP entry."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID based on host
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle network discovery setup."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                self._discovered_devices = await discover_orcomm_devices(
                    self.hass, 
                    user_input["subnet"], 
                    user_input[CONF_USERNAME], 
                    user_input[CONF_PASSWORD]
                )
                
                if not self._discovered_devices:
                    errors["base"] = "no_devices_found"
                else:
                    # Store credentials for later use
                    self._discovery_data = {
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    }
                    return await self.async_step_select_device()
                    
            except InvalidSubnet:
                errors["subnet"] = "invalid_subnet"
            except SubnetTooLarge:
                errors["subnet"] = "subnet_too_large"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during discovery")
                errors["base"] = "discovery_failed"

        return self.async_show_form(
            step_id="discovery",
            data_schema=STEP_DISCOVERY_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection from discovered devices."""
        if user_input is not None:
            selected_host = user_input["device"]
            
            # Find the selected device info
            selected_device = next(
                (dev for dev in self._discovered_devices if dev["host"] == selected_host),
                None
            )
            
            if not selected_device:
                return self.async_abort(reason="device_not_found")
            
            # Prepare final configuration data
            config_data = {
                CONF_HOST: selected_host,
                **self._discovery_data
            }
            
            try:
                # Validate the selected device one more time
                info = await validate_input(self.hass, config_data)
            except (CannotConnect, InvalidAuth):
                return self.async_abort(reason="device_connection_failed")
            
            # Set unique ID based on host
            await self.async_set_unique_id(selected_host)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=info["title"],
                data=config_data,
            )

        # Create device selection options
        device_options = {}
        for device in self._discovered_devices:
            label = f"{device['host']}"
            if device["status"] == "authenticated":
                label += f" ({device['devices_count']} devices)"
            else:
                label += " (authentication required)"
            device_options[device["host"]] = label

        data_schema = vol.Schema(
            {
                vol.Required("device"): vol.In(device_options)
            }
        )

        return self.async_show_form(
            step_id="select_device",
            data_schema=data_schema,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidSubnet(HomeAssistantError):
    """Error to indicate invalid subnet format."""


class SubnetTooLarge(HomeAssistantError):
    """Error to indicate subnet is too large for scanning."""