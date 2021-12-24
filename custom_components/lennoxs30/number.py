"""Support for Lennoxs30 outdoor temperature sensor"""
from lennoxs30api.s30exception import S30Exception
from .const import CONF_CLOUD_CONNECTION, MANAGER
from homeassistant.components.number import NumberEntity
from homeassistant.const import (
    CONF_NAME,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from . import DOMAIN, Manager
from homeassistant.core import HomeAssistant
import logging
from homeassistant.helpers.entity import Entity
from lennoxs30api import lennox_system, lennox_zone
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    _LOGGER.debug("number:async_setup_platform enter")
    number_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    # We do not support setting diag level from a cloud connection
    if (
        entry.data[CONF_CLOUD_CONNECTION] == True
        or manager._create_inverter_power == False
    ):
        _LOGGER.debug(
            "async_setup_entry - not cresting diagnosrtic level number because inverter power not enabled"
        )
        return
    for system in manager._api.getSystems():
        number = DiagnosticLevelNumber(hass, manager, system)
        number_list.append(number)

    if len(number_list) != 0:
        async_add_entities(number_list, True)


class DiagnosticLevelNumber(NumberEntity):
    """Set the diagnostic level in the S30."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._myname = self._system.name + "_diagnostic_level"
        self._system.registerOnUpdateCallback(self.update_callback, ["diagLevel"])
        _LOGGER.debug(f"Create DiagnosticLevelNumber myname [{self._myname}]")

    def update_callback(self):
        _LOGGER.debug(f"update_callback DiagnosticLevelNumber myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_DL").replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def max_value(self) -> float:
        return 2

    @property
    def min_value(self) -> float:
        return 0

    @property
    def step(self) -> float:
        return 1

    @property
    def value(self) -> float:
        return self._system.diagLevel

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        try:
            await self._system.set_diagnostic_level(value)
        except S30Exception as e:
            _LOGGER.error(f"DiagnosticLevelNumber::async_set_value [{e.as_string()}]")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }
        return result
