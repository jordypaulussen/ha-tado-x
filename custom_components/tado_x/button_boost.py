"""Button platform for Tado X CK04 Boiler Boost."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TadoXDataUpdateCoordinator


BOOST_DURATION_MINUTES = 30  # standaard boost tijd


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tado X Boost buttons."""
    coordinator: TadoXDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ButtonEntity] = []

    for device in coordinator.data.devices.values():
        if device.device_type == "HEAT_PUMP_OPTIMIZER":
            entities.append(TadoXBoilerBoostButton(coordinator, device.serial_number))

    if entities:
        async_add_entities(entities)


class TadoXBoilerBoostButton(
    CoordinatorEntity[TadoXDataUpdateCoordinator],
    ButtonEntity,
):
    """Button entity to trigger CK04 boiler boost."""

    _attr_has_entity_name = True
    _attr_name = "Boiler Boost"

    def __init__(self, coordinator: TadoXDataUpdateCoordinator, serial_number: str) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._attr_unique_id = f"{serial_number}_boiler_boost"
        self._boost_end: datetime | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device = self.coordinator.data.devices[self._serial_number]
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            manufacturer="Tado",
            model=device.device_type,
            name=f"Tado {device.device_type}",
        )

    @property
    def available(self) -> bool:
        """Button is available if device exists."""
        return self._serial_number in self.coordinator.data.devices

    @property
    def extra_state_attributes(self) -> dict:
        """Optional extra attributes for boost status."""
        return {
            "boost_active": self._boost_end is not None and datetime.utcnow() < self._boost_end,
            "boost_ends_at": self._boost_end.isoformat() if self._boost_end else None,
        }

    async def async_press(self, **kwargs: Any) -> None:
        """Trigger boiler boost via API."""
        api = self.coordinator.api

        # Roep boost aan (de API moet deze functie hebben)
        await api.dhw_boost(duration_minutes=BOOST_DURATION_MINUTES)

        # Update lokale state met timer
        self._boost_end = datetime.utcnow() + timedelta(minutes=BOOST_DURATION_MINUTES)
        self.async_write_ha_state()
