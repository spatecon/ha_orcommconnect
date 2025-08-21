"""Base entity for Orcomm Connect integration."""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import OrcommConnectDataUpdateCoordinator
from .const import DOMAIN


class OrcommConnectEntity(CoordinatorEntity[OrcommConnectDataUpdateCoordinator]):
    """Base entity for Orcomm Connect devices."""

    def __init__(
        self,
        coordinator: OrcommConnectDataUpdateCoordinator,
        device: dict,
        module: dict,
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = device
        self._module = module
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["address"])},
            name=f"Orcomm Device {device['address']}",
            manufacturer="Orcomm",
            model=f"Type {module['type']} ({'Primary' if module['is_primary'] else 'Secondary'})",
            sw_version="1.0",
            via_device=(DOMAIN, "hub"),
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID for the entity."""
        return f"{self._device['address']}_{self._module['channel']}_{self._module['device_uid']}"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        device_name = f"Device {self._device['address']}"
        if self._device["channels"] > 1:
            device_name += f" Ch{self._module['channel']}"
        return device_name

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "address": self._device["address"],
            "mac_address": self._device["mac_address"],
            "channel": self._module["channel"],
            "device_uid": self._module["device_uid"],
            "device_type": self._module["type"],
            "is_primary": self._module["is_primary"],
            "wiring_type": self._module["wiring_type"],
            "last_seen": self._module["last_seen"],
            "multiway_group": self._module["multiway_group"],
        }

    def _get_current_module(self) -> dict:
        """Get the current module data from coordinator."""
        if not self.coordinator.data:
            return self._module
            
        for device in self.coordinator.data:
            if device["address"] == self._device["address"]:
                for module in device["modules"]:
                    if module["device_uid"] == self._module["device_uid"]:
                        return module
        return self._module