# Orcomm Connect Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/elijah/ha-orcommconnect)](https://github.com/elijah/ha-orcommconnect/releases)
[![GitHub](https://img.shields.io/github/license/elijah/ha-orcommconnect)](LICENSE)

A Home Assistant custom integration for controlling Orcomm Connect lighting and switch systems over LAN.

## Features

- **Local Network Control**: Communicates directly with your Orcomm Connect system over your local network
- **Multiple Device Types**: Supports both switches (type 1) and dimmable lights (type 2)
- **Multi-Channel Support**: Handle devices with multiple channels (up to 4 channels per device)
- **Device Location**: Locate/identify devices by making them blink
- **Real-time Updates**: Automatic polling for device state changes
- **Energy Monitoring**: Track energy usage and monitoring data (when available)
- **Multiway Groups**: Support for linked switch groups

## Supported Device Types

- **Switches** (Type 1): Basic on/off functionality
- **Dimmers** (Type 2): On/off with brightness control (0-100%)
- **Multi-channel devices**: Support for devices with up to 4 independent channels
- **Locate buttons**: Make devices blink for identification

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/elijah/ha-orcommconnect` as an Integration
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/elijah/ha-orcommconnect/releases)
2. Extract the contents to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

- Orcomm Connect system accessible on your local network
- Default credentials: username `admin`, password `orcomm` (configurable)
- System running on port 1443 (HTTP)

### Setup

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for "Orcomm Connect"
4. Choose your setup method:

#### Option A: Automatic Discovery (Recommended)
1. Select **"Automatic Discovery"**
2. Enter your network details:
   - **Network Subnet**: Your network in CIDR notation (e.g., `192.168.1.0/24`)
   - **Username**: Authentication username (default: `admin`)
   - **Password**: Authentication password (default: `orcomm`)
3. Click **Submit** to start scanning
4. Select your Orcomm Connect device from the discovered list
5. Click **Submit** to complete setup

#### Option B: Manual Configuration
1. Select **"Manual IP Entry"**
2. Enter your Orcomm Connect system details:
   - **Host**: IP address of your Orcomm Connect system (e.g., `192.168.1.196`)
   - **Username**: Authentication username (default: `admin`)
   - **Password**: Authentication password (default: `orcomm`)
3. Click **Submit**

The integration will automatically discover all connected devices and create appropriate entities.

### Network Discovery Details

The automatic discovery feature:
- Scans the specified subnet for devices responding on port 1443
- Looks for the characteristic "This URI does not exist" response from the root path
- Validates devices by attempting to access the `/devices` endpoint
- Supports subnets up to /22 (1024 addresses) to prevent network overload
- Uses concurrent scanning with rate limiting (20 simultaneous connections)
- Shows device status and device count for authenticated connections

## Entity Types

### Switches
- **Entity Type**: `switch.orcomm_device_[address]_ch[channel]`
- **Controls**: On/Off functionality
- **Device Types**: Type 1 modules

### Lights  
- **Entity Type**: `light.orcomm_device_[address]_ch[channel]`
- **Controls**: On/Off and Brightness (0-100%)
- **Device Types**: Type 2 modules

### Buttons
- **Entity Type**: `button.orcomm_device_[address]_ch[channel]_locate`
- **Function**: Makes the physical device blink for identification
- **Available for**: All device types

## Device Information

Each entity provides additional information in its attributes:

- `address`: Physical device address
- `mac_address`: Device MAC address  
- `channel`: Channel number on multi-channel devices
- `device_uid`: Unique device identifier
- `device_type`: 1 (switch) or 2 (dimmer)
- `is_primary`: Whether this is the primary module
- `wiring_type`: Wiring configuration type
- `last_seen`: Time since last communication (seconds)
- `multiway_group`: Multiway group ID (for linked switches)

## API Endpoints Used

The integration communicates with the following Orcomm Connect API endpoints:

- `GET /devices` - Retrieve all devices and their status
- `POST /device/switch` - Control device power state and brightness
- `POST /device/locate` - Make devices blink for identification

## Troubleshooting

### Connection Issues

1. **Cannot Connect**: Verify the IP address and ensure the Orcomm Connect system is accessible
2. **Authentication Failed**: Check username/password (default: admin/orcomm)
3. **Timeout**: Ensure port 1443 is accessible and not blocked by firewall

### Device Issues

1. **Devices Not Appearing**: Check that devices are properly connected to the Orcomm Connect system
2. **State Not Updating**: Verify network connectivity and check the scan interval setting
3. **Controls Not Working**: Ensure the device supports the requested operation (e.g., brightness for switches)

### Logging

Enable debug logging for detailed troubleshooting:

```yaml
logger:
  default: warning
  logs:
    custom_components.orcommconnect: debug
```

## Configuration Options

You can configure the following options:

- **Scan Interval**: How often to poll for device updates (default: 30 seconds)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This integration is not affiliated with or endorsed by Orcomm. Use at your own risk.