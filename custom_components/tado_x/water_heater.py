import logging
from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_OPERATION_MODE,
)
from homeassistant.const import TEMP_CELSIUS

_LOGGER = logging.getLogger(__name__)
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["tado_x_coordinator"]
    async_add_entities([TadoXDomesticHotWater(coordinator)])

class TadoXDomesticHotWater(WaterHeaterEntity):
    """Tado Domestic Hot Water entity"""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._name = "Tado Domestic Hot Water"

    @property
    def name(self):
        return self._name

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        return self.coordinator.data["heat_pump"]["domesticHotWater"]["currentTemperatureInCelsius"]

    @property
    def target_temperature(self):
        return self.coordinator.data["heat_pump"]["domesticHotWater"]["currentBlockSetpoint"]["setpointValue"]["value"]

    @property
    def min_temp(self):
        return 40.0

    @property
    def max_temp(self):
        return 60.0

    @property
    def supported_features(self):
        return SUPPORT_FLAGS

    @property
    def operation_list(self):
        return ["off", "on", "boost"]

    @property
    def current_operation(self):
        dhw = self.coordinator.data["heat_pump"]["domesticHotWater"]
        if dhw["boostActive"]:
            return "boost"
        if dhw["manualOffActive"]:
            return "off"
        return "on"

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get("temperature")
        if temperature is not None:
            await self.coordinator.tado_x.set_dhw_temperature(temperature)
            await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode):
        dhw = self.coordinator.data["heat_pump"]["domesticHotWater"]
        if operation_mode == "boost":
            await self.coordinator.tado_x.set_dhw_boost(True)
        elif operation_mode == "off":
            await self.coordinator.tado_x.set_dhw_manual_off(True)
        else:
            await self.coordinator.tado_x.set_dhw_boost(False)
            await self.coordinator.tado_x.set_dhw_manual_off(False)
        await self.coordinator.async_request_refresh()
