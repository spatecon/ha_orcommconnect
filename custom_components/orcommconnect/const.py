"""Constants for the Orcomm Connect integration."""

DOMAIN = "orcommconnect"

# Config flow
CONF_HOST = "host"

# Default values
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PORT = 1443
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "orcomm"

# Device types
DEVICE_TYPE_SWITCH = 1
DEVICE_TYPE_DIMMER = 2

# Entity types
ENTITY_SWITCH = "switch"
ENTITY_LIGHT = "light"

# Attributes
ATTR_ADDRESS = "address"
ATTR_MAC_ADDRESS = "mac_address"
ATTR_CHANNEL = "channel"
ATTR_DEVICE_UID = "device_uid"
ATTR_DEVICE_TYPE = "type"
ATTR_IS_PRIMARY = "is_primary"
ATTR_WIRING_TYPE = "wiring_type"
ATTR_LAST_SEEN = "last_seen"
ATTR_MULTIWAY_GROUP = "multiway_group"
ATTR_ENERGY_MONITORING = "energy_monitoring"
ATTR_POWER_STATE = "power_state"
ATTR_BRIGHTNESS = "brightness"