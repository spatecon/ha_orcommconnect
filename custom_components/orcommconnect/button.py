"""Button platform for Orcomm Connect integration."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import OrcommConnectDataUpdateCoordinator
from .const import DOMAIN
from .entity import OrcommConnectEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Orcomm Connect button entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OrcommConnectDataUpdateCoordinator = data["coordinator"]
    api = data["api"]
    devices = data["devices"]

    entities = []
    for device in devices:
        for module in device["modules"]:
            # Create a locate button for each module
            entities.append(OrcommConnectLocateButton(coordinator, api, device, module))

    async_add_entities(entities)


class OrcommConnectLocateButton(OrcommConnectEntity, ButtonEntity):
    """Representation of an Orcomm Connect locate button."""

    def __init__(self, coordinator, api, device, module):
        """Initialize the button."""
        super().__init__(coordinator, device, module)
        self._api = api
        self._attr_icon = "mdi:map-marker-radius"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        base_name = super().name
        return f"{base_name} Locate"

    @property
    def unique_id(self) -> str:
        """Return unique ID for the entity."""
        return f"{super().unique_id}_locate"

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self._api.async_locate_device(
                address=self._device["address"],
                channel=self._module["channel"],
                state=True,
            )
            _LOGGER.info("Locate command sent for device %s channel %s", 
                        self._device["address"], self._module["channel"])
        except Exception as err:
            _LOGGER.error("Failed to locate device %s: %s", self.unique_id, err)