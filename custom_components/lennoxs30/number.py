"""Support for Lennoxs30 outdoor temperature sensor"""
from lennoxs30api.s30exception import S30Exception

from .base_entity import S30BaseEntity
from .const import (
    CONF_CLOUD_CONNECTION,
    MANAGER,
    UNIQUE_ID_SUFFIX_TIMED_VENTILATION_NUMBER,
    VENTILATION_EQUIPMENT_ID,
)
from homeassistant.components.number import NumberEntity
from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    TIME_MINUTES,
)
from . import DOMAIN, Manager
from homeassistant.core import HomeAssistant
import logging
from lennoxs30api import (
    lennox_system,
    LENNOX_CIRCULATE_TIME_MAX,
    LENNOX_CIRCULATE_TIME_MIN,
    LENNOX_VENTILATION_CONTROL_MODE_TIMED,
)
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

    for system in manager._api.getSystems():
        # We do not support setting diag level from a cloud connection
        if manager._api._isLANConnection == False or (
            manager._create_inverter_power == False
            and manager._create_diagnostic_sensors == False
        ):
            _LOGGER.debug(
                "async_setup_entry - not creating diagnostic level number because inverter power not enabled"
            )
        else:
            number = DiagnosticLevelNumber(hass, manager, system)
            number_list.append(number)
        if (
            system.enhancedDehumidificationOvercoolingF_enable == True
            and system.is_none(system.dehumidifierType) == False
        ):
            number = DehumidificationOverCooling(hass, manager, system)
            number_list.append(number)
        number = CirculateTime(hass, manager, system)
        number_list.append(number)

        if (
            system.supports_ventilation()
            and system.ventilationControlMode == LENNOX_VENTILATION_CONTROL_MODE_TIMED
        ):
            number = TimedVentilationNumber(hass, manager, system)
            number_list.append(number)

    if len(number_list) != 0:
        async_add_entities(number_list, True)


class DiagnosticLevelNumber(S30BaseEntity, NumberEntity):
    """Set the diagnostic level in the S30."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_diagnostic_level"
        _LOGGER.debug(f"Create DiagnosticLevelNumber myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass DiagnosticLevelNumber myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallback(self.update_callback, ["diagLevel"])
        await super().async_added_to_hass()

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
            if value == 1:
                _LOGGER.warning(
                    "Diagnostic Level Number - setting to a value of 1 is not recommeded. See https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md"
                )
            if value != 0 and (
                self._system.internetStatus == True
                or self._system.relayServerConnected == True
            ):
                _LOGGER.warning(
                    f"Diagnostic Level Number - setting to a non-zer value is not recommended for systems connected to the lennox cloud internetStatus [{self._system.internetStatus}] relayServerConnected [{self._system.relayServerConnected}] - https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md"
                )
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


class DehumidificationOverCooling(S30BaseEntity, NumberEntity):
    """Set the diagnostic level in the S30."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_dehumidification_overcooling"
        _LOGGER.debug(f"Create DehumidificationOverCooling myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass DehumidificationOverCooling myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "enhancedDehumidificationOvercoolingC_enable",
                "enhancedDehumidificationOvercoolingF_enable",
                "enhancedDehumidificationOvercoolingC",
                "enhancedDehumidificationOvercoolingF",
                "enhancedDehumidificationOvercoolingF_min",
                "enhancedDehumidificationOvercoolingF_max",
                "enhancedDehumidificationOvercoolingF_inc",
                "enhancedDehumidificationOvercoolingC_min",
                "enhancedDehumidificationOvercoolingC_max",
                "enhancedDehumidificationOvercoolingC_inc",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(
            f"update_callback DehumidificationOverCooling myname [{self._myname}]"
        )
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_DOC").replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def unit_of_measurement(self):
        if self._manager._is_metric is False:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def max_value(self) -> float:
        if self._manager._is_metric:
            return self._system.enhancedDehumidificationOvercoolingC_max
        return self._system.enhancedDehumidificationOvercoolingF_max

    @property
    def min_value(self) -> float:
        if self._manager._is_metric:
            return self._system.enhancedDehumidificationOvercoolingC_min
        return self._system.enhancedDehumidificationOvercoolingF_min

    @property
    def step(self) -> float:
        if self._manager._is_metric:
            return self._system.enhancedDehumidificationOvercoolingC_inc
        return self._system.enhancedDehumidificationOvercoolingF_inc

    @property
    def value(self) -> float:
        if self._manager._is_metric:
            return self._system.enhancedDehumidificationOvercoolingC
        return self._system.enhancedDehumidificationOvercoolingF

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        try:
            if self._manager._is_metric:
                await self._system.set_enhancedDehumidificationOvercooling(r_c=value)
            else:
                await self._system.set_enhancedDehumidificationOvercooling(r_f=value)
        except S30Exception as e:
            _LOGGER.error(
                f"DehumidificationOverCooling::async_set_value [{e.as_string()}]"
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }
        return result


class CirculateTime(S30BaseEntity, NumberEntity):
    """Set the diagnostic level in the S30."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_circulate_time"
        _LOGGER.debug(f"Create CirculateTime myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(f"async_added_to_hass CirculateTime myname [{self._myname}]")
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "circulateTime",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(f"update_callback CirculateTime myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_CIRC_TIME").replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def max_value(self) -> float:
        return LENNOX_CIRCULATE_TIME_MAX

    @property
    def min_value(self) -> float:
        return LENNOX_CIRCULATE_TIME_MIN

    @property
    def step(self) -> float:
        return 1.0

    @property
    def value(self) -> float:
        return self._system.circulateTime

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        try:
            await self._system.set_circulateTime(value)
        except S30Exception as e:
            _LOGGER.error(f"CirculateTime::async_set_value [{e.as_string()}]")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }
        return result


class TimedVentilationNumber(S30BaseEntity, NumberEntity):
    """Set timed ventilation."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_timed_ventilation"
        _LOGGER.debug(f"Create TimedVentilationNumber myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass TimedVentilationNumber myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallback(
            self.update_callback, ["ventilationRemainingTime"]
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(f"update_callback TimedVentilationNumber myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (
            self._system.unique_id() + UNIQUE_ID_SUFFIX_TIMED_VENTILATION_NUMBER
        ).replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def max_value(self) -> float:
        return 1440

    @property
    def min_value(self) -> float:
        return 0

    @property
    def step(self) -> float:
        return 1

    @property
    def value(self) -> float:
        return int(self._system.ventilationRemainingTime / 60)

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        _LOGGER.info(f"TimedVentilationNumber set value to [{value}]")
        try:
            value_i = int(value)
            value_seconds = value_i * 60
            await self._system.ventilation_timed(value_seconds)
        except S30Exception as e:
            _LOGGER.error(f"TimedVentilationNumber::async_set_value [{e.as_string()}]")
        except ValueError as v:
            _LOGGER.error(
                f"TimedVentilationNumber::async_set_value invalid value [{value}] ValueError [{v}]"
            )

    @property
    def unit_of_measurement(self):
        return TIME_MINUTES

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        equip_device_map = self._manager.system_equip_device_map.get(self._system.sysId)
        if equip_device_map != None:
            device = equip_device_map.get(VENTILATION_EQUIPMENT_ID)
            if device != None:
                return {
                    "identifiers": {(DOMAIN, device.unique_name)},
                }
            _LOGGER.warning(
                f"Unable to find VENTILATION_EQUIPMENT_ID in device map, please raise an issue"
            )
        else:
            _LOGGER.error(
                f"No equipment device map found for sysId [{self._system.sysId}] equipment VENTILATION_EQUIPMENT_ID, please raise an issue"
            )
        return {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }
