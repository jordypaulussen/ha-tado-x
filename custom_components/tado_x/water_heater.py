"""Tado X Water Heater (Boiler) integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
    STATE_OFF,
    STATE_ON,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import TadoXDataUpdateCoordinator, TadoXDevice
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tado X water heaters (boilers) from a config entry."""
    coordinator: TadoXDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Find all devices that are boilers/water heaters
    boiler_devices = [
        device
        for device in coordinator.data.other_devices
        if device.device_type in ("HEATING_WATER_HEATER", "WATER_HEATER", "BOILER")
    ]

    entities = [
        TadoXWaterHeater(coordinator=coordinator, device=device)
        for device in boiler_devices
    ]

    if not entities:
        _LOGGER.info("No Tado X water heaters found for this home")

    async_add_entities(entities, update_before_add=True)


class TadoXWaterHeater(WaterHeaterEntity):
    """Representation of a Tado X Water Heater (Boiler)."""

    _attr_supported_features = SUPPORT_TARGET_TEMPERATURE

    def __init__(self, coordinator: TadoXDataUpdateCoordinator, device: TadoXDevice) -> None:
        """Initialize the water heater."""
        self.coordinator = coordinator
        self.device = device
        self._attr_name = f"{coordinator.home_name} {device.device_type}"
        self._attr_unique_id = f"{device.serial_number}_water_heater"

    @property
    def current_temperature(self) -> float | None:
        """Return current water temperature in °C."""
        return self.device.temperature_measured

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        # Tado water heater always keeps min 40°C, use API setting if available
        return getattr(self.device, "temperature_target", None)

    @property
    def min_temp(self) -> float:
        """Return minimum temperature allowed."""
        return 40.0

    @property
    def max_temp(self) -> float:
        """Return maximum temperature allowed."""
        return 65.0

    @property
    def is_on(self) -> bool:
        """Return True if the boiler is on."""
        return self.device.temperature_measured is not None and self.device.temperature_measured >= 40.0

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        target = kwargs.get("temperature")
        if target is None:
            return

        # Clamp target to allowed range
        target = max(self.min_temp, min(self.max_temp, target))

        try:
            await self.coordinator.api.set_boiler_temperature(self.device.serial_number, target)
            _LOGGER.info("Set boiler %s temperature to %.1f°C", self.device.serial_number, target)
            # Refresh coordinator data to reflect change
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set boiler temperature for %s: %s", self.device.serial_number, err)

    async def async_update(self) -> None:
        """Request coordinator to refresh data."""
        await self.coordinator.async_request_refresh()
