"""Support for Tado X water heater (boiler)."""

from __future__ import annotations
import logging

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import TEMP_CELSIUS

from .coordinator import TadoXDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Tado X water heater platform."""
    coordinator: TadoXDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Zoek boiler/water_heater devices
    water_heaters = []
    for device in coordinator.data.other_devices:
        if device.device_type.lower() in ["water_heater", "boiler"]:
            water_heaters.append(TadoXWaterHeater(coordinator, device))

    if not water_heaters:
        _LOGGER.info("Geen water_heater devices gevonden voor Tado X")
        return

    async_add_entities(water_heaters)


class TadoXWaterHeater(WaterHeaterEntity):
    """Representation of a Tado X water heater."""

    def __init__(self, coordinator: TadoXDataUpdateCoordinator, device):
        self.coordinator = coordinator
        self.device = device
        self._attr_name = f"Tado Boiler {device.serial_number}"
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE
        self._attr_temperature_unit = TEMP_CELSIUS

    @property
    def current_temperature(self):
        return self.device.temperature_measured

    @property
    def target_temperature(self):
        return getattr(self.device, "target_temperature", None)

    @property
    def is_on(self):
        return self.device.connection_state == "CONNECTED"

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        if temp is not None:
            # Zet de boiler temperatuur via de coordinator API
            await self.coordinator.api.set_boiler_temperature(
                self.device.serial_number, temp
            )
            await self.coordinator.async_request_refresh()
