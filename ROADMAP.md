# Roadmap

This document tracks planned features and enhancements for the Tado X Home Assistant integration.

## Planned Features

### P1 - Critical Priority

- **🔥 Local API Mode** - Control Tado devices locally via HomeKit protocol
  - Zero cloud dependency for core operations
  - No API rate limits
  - Instant response times
  - *Note: Requires HomeKit bridge re-pairing, same network*

### P2 - High Priority

- **📊 Energy IQ Dashboard** - Gas consumption and cost tracking
  - Daily/weekly/monthly consumption sensors
  - Cost estimates based on configured tariffs
  - Comparison with previous periods

- **📅 Schedule Management** - Full schedule control from Home Assistant
  - Read current heating schedules
  - Modify schedules via service calls
  - Copy/duplicate schedules between days
  - Switch between schedule profiles

- **📈 Heating Statistics** - Advanced heating analytics
  - Historical heating time per room
  - Heating efficiency metrics
  - Monthly reports with trends

### P3 - Medium Priority

- **🌡️ Historic Data** - Historical temperature, humidity, and heating data
  - Temperature graphs in HA
  - Long-term statistics integration

- **💧 Hot Water Control** - Dedicated water heater support
  - Water heater entity
  - Timer for hot water schedules
  - Boost hot water service

- **🤖 Smart Schedule Suggestions** - AI-powered optimization
  - Analyze usage patterns
  - Suggest schedule improvements
  - Integration with HA history

### P4 - Low Priority

- **📍 Away Radius Configuration** - Configure geofencing radius
- **❄️ AC Support** - Air conditioning control (if requested)
  - Fan speed control
  - Swing adjustment
  - DRY/FAN/AUTO modes
- **📺 Display Messages** - Send messages to thermostat displays
- **⏰ Early Start Settings** - Control pre-heating behavior

---

## Completed

See [CHANGELOG](https://github.com/exabird/ha-tado-x/releases) for completed features by version.

**Recent highlights:**
- v1.8.1 - Fix entity naming, add flow temp toggle option
- v1.8.0 - Flow Temperature Optimization (max flow temp control, auto-adaptation switch)
- v1.7.1 - Fix set_climate_timer validation for non-Tado entities
- v1.7.0 - Home presence sensors, select entity, set_climate_timer service, graceful 429 rate limit handling
- v1.6.7 - Weather sensor fix (all states supported)
- v1.6.6 - Fix HVAC mode OFF vs AUTO detection
- v1.6.5 - Temperature offset sensor
- v1.6.4 - Fix OptionsFlow for HA 2024.x
- v1.6.0 - Weather sensors, air comfort, mobile tracking, heating time
- v1.5.0 - Quick actions, Energy IQ tariff management
- v1.4.0 - Child lock, open window controls
- v1.3.0 - API usage monitoring, smart polling

---

## Won't Implement

*None currently*

---

## Support Development

If you find this integration useful, consider [buying me a coffee ☕](https://buymeacoffee.com/exabird) to support ongoing development!

Your support helps prioritize and accelerate the features on this roadmap.

---

## How to Request Features

Open an issue using the [Feature Request template](https://github.com/exabird/ha-tado-x/issues/new?template=feature_request.md).
