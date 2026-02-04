# Roadmap

This document tracks planned features and enhancements for the Tado X Home Assistant integration.

## Planned Features

### P1 - Critical Priority

- **🔥 Local Control Mode** - Control Tado X devices locally via Thread/Matter
  - Zero cloud dependency - works even when Tado servers are down
  - No API rate limits - unlimited updates
  - Ultra-fast response times (~10-50ms vs ~500ms cloud)
  - Real-time state updates
  - Full local temperature control

  **How it works:** Tado X devices use the Thread protocol with Matter support. The Bridge X acts as a Thread Border Router, enabling direct IPv6 communication with all devices on your local network. Tado officially supports local control via Matter: *"The devices continue to work even without a connection to the Tado cloud."*

  **What's possible:**
  - Temperature control ✓
  - On/Off switching ✓
  - Home/Away modes ✓
  - Heating schedules (Matter 1.4+) ✓
  - Real-time state monitoring ✓

  **Technical approaches:**
  1. **Matter integration** - Native Matter protocol (most promising)
  2. **HomeKit bridge** - Via [TadoLocal](https://github.com/AmpScm/TadoLocal) project
  3. **Thread direct** - Direct IPv6 communication with Thread devices

  **Requirements:**
  - Bridge X and Home Assistant on same local network
  - One-time Matter/HomeKit pairing setup

  **Status:** Research phase - investigating Matter and Thread integration options

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

- **⏸️ Disable Polling Option** - Allow users to completely disable API polling
  - Add checkbox or "0" option in scan interval to disable polling
  - Use case: Users who only need the integration for services (temperature offset) and use Matter for state
  - Saves API quota for custom automations
  - Requested by: @LeroyK (#41), supported by @rofra

- **🔥 Zone Controller Toggle (Passive Heating Mode)** - Per-room control of boiler "call for heat"
  - Toggle Zone Controller association per room to enable "passive heating"
  - When disabled: room valves open based on setpoints but don't trigger the boiler relay
  - Use case: Let rooms benefit from heat generated for other rooms without independent boiler calls
  - New select entity or switch per room to control Zone Controller state
  - Requested by: @polamoros (#29)

- **🏷️ Improved Flow Sensor Naming** - ~~More descriptive entity names for flow temperature sensors~~ ✅ Fixed in v1.8.5
  - ~~Rename `_none` entities to include "flow" prefix~~
  - Requested by: @TexTown (#26), @xiic (#21)

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
