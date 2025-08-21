# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-21

### Added
- Initial release of Orcomm Connect Home Assistant integration
- Support for switch devices (Type 1) with on/off functionality
- Support for dimmer devices (Type 2) with brightness control
- Multi-channel device support (up to 4 channels per device)
- Device location/identification functionality via locate buttons
- Basic authentication support (username/password)
- Automatic device discovery from Orcomm Connect system
- **Network Discovery Feature**: Automatic subnet scanning to find Orcomm Connect devices
  - CIDR subnet notation support (e.g., 192.168.1.0/24)
  - Concurrent scanning with rate limiting
  - Device validation using signature HTTP responses
  - Support for subnets up to /22 (1024 addresses)
  - Fallback to manual configuration option
- Real-time device state polling and updates
- Energy monitoring data attributes
- Multiway group support for linked switches
- Comprehensive device information in entity attributes
- Configuration flow for easy setup with choice between automatic discovery and manual entry
- HACS compatibility
- Full Home Assistant 2023.2+ compatibility

### Technical Features
- HTTP API communication over port 1443
- JSON-based device control and status
- Coordinator-based data updates
- Proper entity state management
- Device registry integration
- Translation support (English)
- Error handling and logging
- Async/await throughout

### API Endpoints
- `GET /devices` - Device discovery and status
- `POST /device/switch` - Device control (power/brightness)
- `POST /device/locate` - Device identification

### Entity Types
- Switch entities for Type 1 devices
- Light entities for Type 2 devices  
- Button entities for device location

### Configuration
- Simple config flow setup
- Host IP address configuration
- Username/password authentication
- Scan interval options