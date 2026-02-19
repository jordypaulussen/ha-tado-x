"""Switch platform for Tado X."""

from __future__ import annotations
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TadoXDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tado X switches."""
    coordinator: TadoXDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SwitchEntity] = []

    # Detect CK04 devices (Heat Pump Optimizer)
    for device in coordinator.data.devices.values():
        if device.device_type.upper() == "CK04":
            entities.append(TadoXHeatPumpBoilerSwitch(coordinator, device.serial_number))

    if entities:
        async_add_entities(entities)

class TadoXHeatPumpBoilerSwitch(
    CoordinatorEntity[TadoXDataUpdateCoordinator],
    SwitchEntity,
):
    """Switch entity to control Tado Heat Pump DHW."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator: TadoXDataUpdateCoordinator, serial_number: str) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._attr_unique_id = f"{serial_number}_dhw"
        self._attr_name = "Heatpump Boiler DHW"

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
    def is_on(self) -> bool | None:
        """Return the current switch state from coordinator."""
        device = self.coordinator.data.devices.get(self._serial_number)
        if device is None:
            return None
        return getattr(device, "dhw_active", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable domestic hot water."""
        await self.coordinator.api.dhw_on()
        device = self.coordinator.data.devices.get(self._serial_number)
        if device:
            device.dhw_active = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable domestic hot water."""
        await self.coordinator.api.dhw_off()
        device = self.coordinator.data.devices.get(self._serial_number)
        if device:
            device.dhw_active = False
        self.async_write_ha_state()
