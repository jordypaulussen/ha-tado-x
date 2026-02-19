from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import TadoXDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the robust Tado Heat Pump Boiler switch."""
    coordinator: TadoXDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [TadoXHeatPumpBoilerSwitchOverride(coordinator)]
    async_add_entities(entities)


class TadoXHeatPumpBoilerSwitchOverride(SwitchEntity):
    """Switch to control Tado Heat Pump DHW directly, bypassing coordinator."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator: TadoXDataUpdateCoordinator) -> None:
        self.coordinator = coordinator
        self._attr_name = "Heatpump Boiler DHW Override"
        self._attr_unique_id = f"{coordinator.home_id}_dhw_override"
        self._is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.home_id}_dhw_override")},
            manufacturer="Tado",
            model="Heat Pump Optimizer (CK04)",
            name="Tado Heat Pump",
        )

    @property
    def is_on(self) -> bool:
        """Return current state."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on DHW directly."""
        try:
            await self.coordinator.api.dhw_on()
            self._is_on = True
            self.async_write_ha_state()
        except Exception as e:
            self._is_on = False
            self.async_write_ha_state()
            raise e

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off DHW directly."""
        try:
            await self.coordinator.api.dhw_off()
            self._is_on = False
            self.async_write_ha_state()
        except Exception as e:
            self._is_on = True
            self.async_write_ha_state()
            raise e
