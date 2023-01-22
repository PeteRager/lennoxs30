"""Support for Lennoxs30 outdoor temperature sensor"""
# pylint: disable=global-statement
# pylint: disable=broad-except
# pylint: disable=unused-argument
# pylint: disable=line-too-long
# pylint: disable=invalid-name
from typing import Any
import logging


from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30exception import S30Exception
from lennoxs30api.s30api_async import (
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    LENNOX_DEHUMIDIFICATION_MODE_HIGH,
    LENNOX_DEHUMIDIFICATION_MODE_MEDIUM,
    LENNOX_DEHUMIDIFICATION_MODE_AUTO,
    lennox_system,
    lennox_zone,
)
from lennoxs30api.lennox_equipment import (
    LENNOX_EQUIPMENT_PARAMETER_FORMAT_RADIO,
    lennox_equipment_parameter,
    lennox_equipment,
)

from .helpers import (
    helper_create_equipment_entity_name,
    helper_get_equipment_device_info,
    helper_get_parameter_extra_attributes,
)

from .base_entity import S30BaseEntityMixin
from .const import LOG_INFO_SELECT_ASYNC_SELECT_OPTION, MANAGER, UNIQUE_ID_SUFFIX_EQ_PARAM_SELECT
from . import DOMAIN, Manager


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup the select entities"""
    _LOGGER.debug("number:async_setup_platform enter")

    select_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager.api.system_list:
        if system.is_none(system.dehumidifierType) is False:
            _LOGGER.debug("Create DehumidificationModeSelect system [%s], system.sysId")
            sel = DehumidificationModeSelect(hass, manager, system)
            select_list.append(sel)
        for zone in system.zone_list:
            if zone.is_zone_active():
                if zone.dehumidificationOption or zone.humidificationOption:
                    _LOGGER.debug("Create HumiditySelect [%s] zone [%s]", system.sysId, zone.name)
                    climate = HumidityModeSelect(hass, manager, system, zone)
                    select_list.append(climate)

        if manager.create_equipment_parameters:
            for equipment in system.equipment.values():
                for parameter in equipment.parameters.values():
                    if parameter.enabled and parameter.descriptor == LENNOX_EQUIPMENT_PARAMETER_FORMAT_RADIO:
                        select = EquipmentParameterSelect(hass, manager, system, equipment, parameter)
                        select_list.append(select)

    if len(select_list) != 0:
        async_add_entities(select_list, True)


class HumidityModeSelect(S30BaseEntityMixin, SelectEntity):
    """Set the humidity mode"""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
        zone: lennox_zone,
    ):
        super().__init__(manager, system)
        self.hass: HomeAssistant = hass
        self._zone = zone
        self._myname = self._system.name + "_" + self._zone.name + "_humidity_mode"
        _LOGGER.debug("Create HumidityModeSelect myname [%s]", self._myname)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass HumidityModeSelect myname [%s]", self._myname)
        self._zone.registerOnUpdateCallback(
            self.zone_update_callback,
            [
                "humidityMode",
            ],
        )
        self._system.registerOnUpdateCallback(
            self.system_update_callback,
            [
                "zoningMode",
            ],
        )
        await super().async_added_to_hass()

    def zone_update_callback(self):
        """Callback for zone updates"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "zone_update_callback HumidityModeSelect myname [%s] humidityMode [%s],",
                self._myname,
                self._zone.humidityMode,
            )
        self.schedule_update_ha_state()

    def system_update_callback(self):
        """Callback for system updates"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "system_update_callback HumidityModeSelect myname [%s] system zoning mode [%s]",
                self._myname,
                self._system.zoningMode,
            )
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return self._zone.unique_id + "_HMS"

    @property
    def name(self):
        return self._myname

    @property
    def current_option(self) -> str:
        if self._zone.is_zone_disabled:
            return None
        return self._zone.humidityMode

    @property
    def options(self) -> list:
        opt_list = []
        if self._zone.is_zone_disabled:
            return opt_list
        if self._zone.dehumidificationOption:
            opt_list.append(LENNOX_HUMIDITY_MODE_DEHUMIDIFY)
        if self._zone.humidificationOption:
            opt_list.append(LENNOX_HUMIDITY_MODE_HUMIDIFY)
        opt_list.append(LENNOX_HUMIDITY_MODE_OFF)
        return opt_list

    async def async_select_option(self, option: str) -> None:
        _LOGGER.info(LOG_INFO_SELECT_ASYNC_SELECT_OPTION, self.__class__.__name__, self._myname, option)
        if self._zone.is_zone_disabled:
            raise HomeAssistantError(f"Unable to control humidity mode as zone [{self._myname}] is disabled")
        try:
            await self._zone.setHumidityMode(option)
        except S30Exception as ex:
            raise HomeAssistantError(f"select_option [{self._myname}] [{ex.as_string()}]") from ex
        except Exception as ex:
            raise HomeAssistantError(
                f"select_option unexpected exception, please log issue, [{self._myname}] exception [{ex}]"
            ) from ex

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
        }
        return result


class DehumidificationModeSelect(S30BaseEntityMixin, SelectEntity):
    """Set the humidity mode"""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
    ):
        super().__init__(manager, system)
        self.hass: HomeAssistant = hass
        self._myname = self._system.name + "_dehumidification_mode"
        _LOGGER.debug("Create DehumidificationModeSelect myname [%s]", self._myname)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass DehumidificationModeSelect myname %s]", self._myname)
        self._system.registerOnUpdateCallback(
            self.system_update_callback,
            [
                "dehumidificationMode",
            ],
        )
        await super().async_added_to_hass()

    def system_update_callback(self):
        """Callback for system updates"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "system_update_callback DehumidificationModeSelect myname [%s] dehumidification_mode [%s]",
                self._myname,
                self._system.dehumidificationMode,
            )
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return self._system.unique_id + "_DHMS"

    @property
    def name(self):
        return self._myname

    @property
    def current_option(self) -> str:
        if self._system.dehumidificationMode == LENNOX_DEHUMIDIFICATION_MODE_HIGH:
            return "max"
        if self._system.dehumidificationMode == LENNOX_DEHUMIDIFICATION_MODE_MEDIUM:
            return "normal"
        if self._system.dehumidificationMode == LENNOX_DEHUMIDIFICATION_MODE_AUTO:
            return "climate IQ"
        return None

    @property
    def options(self) -> list:
        return ["normal", "max", "climate IQ"]

    async def async_select_option(self, option: str) -> None:
        _LOGGER.info(LOG_INFO_SELECT_ASYNC_SELECT_OPTION, self.__class__.__name__, self._myname, option)
        mode = None
        if option == "max":
            mode = LENNOX_DEHUMIDIFICATION_MODE_HIGH
        elif option == "normal":
            mode = LENNOX_DEHUMIDIFICATION_MODE_MEDIUM
        elif option == "climate IQ":
            mode = LENNOX_DEHUMIDIFICATION_MODE_AUTO
        else:
            raise HomeAssistantError(
                f"DehumidificationModeSelect select option - invalid mode [{option}] requested must be in [normal, climate IQ, max]"
            )
        try:
            await self._system.set_dehumidificationMode(mode)
        except S30Exception as ex:
            raise HomeAssistantError(f"select_option [{self._myname}] [{ex.as_string()}]") from ex
        except Exception as ex:
            raise HomeAssistantError(
                f"select_option unexpected exception, please log issue, [{self._myname}] exception [{ex}]"
            ) from ex

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }
        return result


class EquipmentParameterSelect(S30BaseEntityMixin, SelectEntity):
    """Set the humidity mode"""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
        equipment: lennox_equipment,
        parameter: lennox_equipment_parameter,
    ):
        super().__init__(manager, system)
        self.hass: HomeAssistant = hass
        self.equipment = equipment
        self.parameter = parameter
        self._myname = helper_create_equipment_entity_name(system, equipment, parameter.name, prefix="par")
        _LOGGER.debug("Create EquipmentParameterSelect myname [%s]", self._myname)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass EquipmentParameterSelect myname [%s]", self._myname)
        self._system.registerOnUpdateCallbackEqParameters(
            self.eq_par_update_callback,
            [f"{self.equipment.equipment_id}_{self.parameter.pid}"],
        )
        await super().async_added_to_hass()

    def eq_par_update_callback(self, pid: str):
        """Callback for equipment parameter updates"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("system_update_callback EquipmentParameterSelect myname [%s]  [%s]", self._myname, pid)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (
            f"{self._system.unique_id}_{UNIQUE_ID_SUFFIX_EQ_PARAM_SELECT}_{self.equipment.equipment_id}_{self.parameter.pid}"
        ).replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def current_option(self) -> str:
        try:
            return self.parameter.radio[int(self.parameter.value)]
        except Exception:
            _LOGGER.error(
                "EquipmentParameterSelect unable to find current radio option value [%s] pid [%s] radio [%s]",
                self.parameter.value,
                self.parameter.pid,
                self.parameter.radio.items(),
            )
            return None

    @property
    def options(self) -> list:
        opts = []
        for i in self.parameter.radio.values():
            opts.append(i)
        return opts

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        _LOGGER.info(LOG_INFO_SELECT_ASYNC_SELECT_OPTION, self.__class__.__name__, self._myname, option)

        if self._manager.parameter_safety_on(self._system.sysId):
            raise HomeAssistantError(f"Unable to set parameter [{self._myname}] parameter safety switch is on")

        try:
            await self._system.set_equipment_parameter_value(self.equipment.equipment_id, self.parameter.pid, option)
        except S30Exception as ex:
            raise HomeAssistantError(f"select_option [{self._myname}] [{option}] [{ex.as_string()}]") from ex
        except Exception as ex:
            raise HomeAssistantError(
                f"select_option unexpected exception, please log issue, [{self._myname}] [{option}] exception [{ex}]"
            ) from ex

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return helper_get_equipment_device_info(self._manager, self._system, self.equipment.equipment_id)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return helper_get_parameter_extra_attributes(self.equipment, self.parameter)
