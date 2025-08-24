"""Light platform for Orcomm Connect integration."""
import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import OrcommConnectDataUpdateCoordinator
from .const import DEVICE_TYPE_DIMMER, DOMAIN
from .entity import OrcommConnectEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Orcomm Connect light entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OrcommConnectDataUpdateCoordinator = data["coordinator"]
    api = data["api"]
    devices = data["devices"]

    entities = []
    for device in devices:
        for module in device["modules"]:
            # Only create light entities for dimmer type devices
            if module["type"] == DEVICE_TYPE_DIMMER:
                entities.append(OrcommConnectLight(coordinator, api, device, module))

    async_add_entities(entities)


class OrcommConnectLight(OrcommConnectEntity, LightEntity):
    """Representation of an Orcomm Connect light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator, api, device, module):
        """Initialize the light."""
        super().__init__(coordinator, device, module)
        self._api = api

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        current_module = self._get_current_module()
        return current_module.get("power_state", False)

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        current_module = self._get_current_module()
        brightness_percent = current_module.get("brightness", 0)
        if brightness_percent is None:
            return None
        # Convert from 0-100% to 0-255
        return int(brightness_percent * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        brightness_percent = None
        
        if brightness is not None:
            # Convert from 0-255 to 0-100%
            brightness_percent = int(brightness * 100 / 255)
        else:
            # If no brightness specified, always default to 100%
            brightness_percent = 100

        try:
            await self._api.async_switch_device(
                device_uid=self._module["device_uid"],
                power_state=True,
                brightness=brightness_percent,
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on light %s: %s", self.unique_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self._api.async_switch_device(
                device_uid=self._module["device_uid"],
                power_state=False,
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off light %s: %s", self.unique_id, err)