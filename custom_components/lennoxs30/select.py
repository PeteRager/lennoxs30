"""Support for Lennoxs30 outdoor temperature sensor"""
from typing import Any
from lennoxs30api.s30exception import S30Exception

from custom_components.lennoxs30.helpers import (
    helper_create_equipment_entity_name,
    helper_get_equipment_device_info,
    helper_get_parameter_extra_attributes,
)

from .base_entity import S30BaseEntity
from .const import MANAGER, UNIQUE_ID_SUFFIX_EQ_PARAM_SELECT
from homeassistant.components.select import SelectEntity
from . import DOMAIN, Manager
from homeassistant.core import HomeAssistant
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import (
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    LENNOX_DEHUMIDIFICATION_MODE_HIGH,
    LENNOX_DEHUMIDIFICATION_MODE_MEDIUM,
    LENNOX_DEHUMIDIFICATION_MODE_AUTO,
    lennox_system,
    lennox_zone,
    EC_BAD_PARAMETERS,
)

from lennoxs30api.lennox_equipment import (
    LENNOX_EQUIPMENT_PARAMETER_FORMAT_RADIO,
    lennox_equipment_parameter,
    lennox_equipment,
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    _LOGGER.debug("number:async_setup_platform enter")

    select_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager._api.getSystems():
        if system.is_none(system.dehumidifierType) == False:
            _LOGGER.debug(
                f"Create DehumidificationModeSelect [{system.sysId}] system [{system.sysId}]"
            )
            sel = DehumidificationModeSelect(hass, manager, system)
            select_list.append(sel)
        for zone in system.getZones():
            if zone.is_zone_active() == True:
                if (
                    zone.dehumidificationOption == True
                    or zone.humidificationOption == True
                ):
                    _LOGGER.debug(
                        f"Create HumiditySelect [{system.sysId}] zone [{zone.name}]"
                    )
                    climate = HumidityModeSelect(hass, manager, system, zone)
                    select_list.append(climate)

        if manager._create_equipment_parameters == True:
            for equipment in system.equipment.values():
                for parameter in equipment.parameters.values():
                    if (
                        parameter.enabled == True
                        and parameter.descriptor
                        == LENNOX_EQUIPMENT_PARAMETER_FORMAT_RADIO
                    ):
                        select = EquipmentParameterSelect(
                            hass, manager, system, equipment, parameter
                        )
                        select_list.append(select)

    if len(select_list) != 0:
        async_add_entities(select_list, True)


class HumidityModeSelect(S30BaseEntity, SelectEntity):
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
        _LOGGER.debug(f"Create HumidityModeSelect myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(f"async_added_to_hass HumidityModeSelect myname [{self._myname}]")
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
        _LOGGER.debug(
            f"zone_update_callback HumidityModeSelect myname [{self._myname}] humidityMode [{self._zone.humidityMode}]"
        )
        self.schedule_update_ha_state()

    def system_update_callback(self):
        _LOGGER.debug(
            f"system_update_callback HumidityModeSelect myname [{self._myname}] system zoning mode [{self._system.zoningMode}]"
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
        if self._zone.is_zone_disabled == True:
            return None
        return self._zone.humidityMode

    @property
    def options(self) -> list:
        list = []
        if self._zone.is_zone_disabled == True:
            return list
        if self._zone.dehumidificationOption == True:
            list.append(LENNOX_HUMIDITY_MODE_DEHUMIDIFY)
        if self._zone.humidificationOption == True:
            list.append(LENNOX_HUMIDITY_MODE_HUMIDIFY)
        list.append(LENNOX_HUMIDITY_MODE_OFF)
        return list

    async def async_select_option(self, option: str) -> None:
        try:
            if self._zone.is_zone_disabled == True:
                raise S30Exception(
                    f"Unable to control humidity mode as zone [{self._myname}] is disabled",
                    EC_BAD_PARAMETERS,
                    2,
                )
            await self._zone.setHumidityMode(option)
        except S30Exception as e:
            _LOGGER.error("HumidityModeSelect async_select_option " + e.as_string())
        except Exception as e:
            _LOGGER.exception(
                "HumidityModeSelect async_select_option - unexpected exception please raise an issue"
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
        }
        return result


class DehumidificationModeSelect(S30BaseEntity, SelectEntity):
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
        _LOGGER.debug(f"Create DehumidificationModeSelect myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass DehumidificationModeSelect myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallback(
            self.system_update_callback,
            [
                "dehumidificationMode",
            ],
        )
        await super().async_added_to_hass()

    def system_update_callback(self):
        _LOGGER.debug(
            f"system_update_callback DehumidificationModeSelect myname [{self._myname}] dehumidification_mode [{self._system.dehumidificationMode}]"
        )
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return self._system.unique_id() + "_DHMS"

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
        list = ["normal", "max", "climate IQ"]
        return list

    async def async_select_option(self, option: str) -> None:
        try:
            mode = None
            if option == "max":
                mode = LENNOX_DEHUMIDIFICATION_MODE_HIGH
            elif option == "normal":
                mode = LENNOX_DEHUMIDIFICATION_MODE_MEDIUM
            elif option == "climate IQ":
                mode = LENNOX_DEHUMIDIFICATION_MODE_AUTO
            else:
                _LOGGER.error(
                    f"DehumidificationModeSelect select option - invalid mode [{option}] requested must be in [normal, climate IQ, max]"
                )
                return
            await self._system.set_dehumidificationMode(mode)
        except S30Exception as e:
            _LOGGER.error(
                "DehumidificationModeSelect async_select_option " + e.as_string()
            )
        except Exception as e:
            _LOGGER.exception(
                "DehumidificationModeSelect async_select_option unexpected exception please log an issue"
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }
        return result


class EquipmentParameterSelect(S30BaseEntity, SelectEntity):
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
        self._myname = helper_create_equipment_entity_name(
            system, equipment, parameter.name, prefix="par"
        )
        _LOGGER.debug(f"Create EquipmentParameterSelect myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass EquipmentParameterSelect myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallbackEqParameters(
            self.eq_par_update_callback,
            [f"{self.equipment.equipment_id}_{self.parameter.pid}"],
        )
        await super().async_added_to_hass()

    def eq_par_update_callback(self, id: str):
        _LOGGER.debug(
            f"system_update_callback EquipmentParameterSelect myname [{self._myname}]  [{id}]"
        )
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (
            f"{self._system.unique_id()}_{UNIQUE_ID_SUFFIX_EQ_PARAM_SELECT}_{self.equipment.equipment_id}_{self.parameter.pid}"
        ).replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def current_option(self) -> str:
        try:
            return self.parameter.radio[int(self.parameter.value)]
        except Exception as e:
            _LOGGER.error(
                f"EquipmentParameterSelect unable to find current radio option value [{self.parameter.value}] pid [{self.parameter.pid}] radio [{self.parameter.radio.items()}]"
            )
            return None

    @property
    def options(self) -> list:
        l = []
        for i in self.parameter.radio.values():
            l.append(i)
        return l

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        _LOGGER.info(
            f"EquipmentParameterSelect [{self._myname}] set value to [{option}] equipment_id [{self.equipment.equipment_id}] pid [{self.parameter.pid}]"
        )

        if self._manager.parameter_safety_on(self._system.sysId):
            raise HomeAssistantError(
                f"Unable to set parameter [{self._myname}] parameter safety switch is on"
            )

        try:
            await self._system.set_equipment_parameter_value(
                self.equipment.equipment_id, self.parameter.pid, option
            )
        except S30Exception as e:
            _LOGGER.error(
                f"EquipmentParameterSelect::async_select_option S30Exception [{self._myname}] set value to [{option}] equipment_id[{self.equipment.equipment_id}] pid [{self.parameter.pid}] [{e.as_string()}]"
            )
        except Exception as e:
            _LOGGER.exception(
                f"EquipmentParameterSelect::async_select_option unexpected exception, please log issue, [{self._myname}] set value to [{option}] equipment_id[{self.equipment.equipment_id}] pid [{self.parameter.pid}] exception [{e}]"
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return helper_get_equipment_device_info(
            self._manager, self._system, self.equipment.equipment_id
        )

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return helper_get_parameter_extra_attributes(self.equipment, self.parameter)
