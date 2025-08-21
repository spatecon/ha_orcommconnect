"""Switch platform for Orcomm Connect integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import OrcommConnectDataUpdateCoordinator
from .const import DEVICE_TYPE_SWITCH, DOMAIN
from .entity import OrcommConnectEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Orcomm Connect switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OrcommConnectDataUpdateCoordinator = data["coordinator"]
    api = data["api"]
    devices = data["devices"]

    entities = []
    for device in devices:
        for module in device["modules"]:
            # Only create switch entities for switch type devices
            if module["type"] == DEVICE_TYPE_SWITCH:
                entities.append(OrcommConnectSwitch(coordinator, api, device, module))

    async_add_entities(entities)


class OrcommConnectSwitch(OrcommConnectEntity, SwitchEntity):
    """Representation of an Orcomm Connect switch."""

    def __init__(self, coordinator, api, device, module):
        """Initialize the switch."""
        super().__init__(coordinator, device, module)
        self._api = api

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        current_module = self._get_current_module()
        return current_module.get("power_state", False)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        try:
            await self._api.async_switch_device(
                device_uid=self._module["device_uid"],
                power_state=True,
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on switch %s: %s", self.unique_id, err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        try:
            await self._api.async_switch_device(
                device_uid=self._module["device_uid"],
                power_state=False,
            )
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off switch %s: %s", self.unique_id, err)