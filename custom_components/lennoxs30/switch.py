"""Support for Lennoxs30 ventilation and allergend defender switches"""
import asyncio
from typing import Any

from .base_entity import S30BaseEntityMixin
from .const import (
    MANAGER,
    UNIQUE_ID_SUFFIX_PARAMETER_SAFETY_SWITCH,
    VENTILATION_EQUIPMENT_ID,
)
from . import Manager
from homeassistant.core import HomeAssistant
import logging
from lennoxs30api import lennox_system
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    _LOGGER.debug("switch:async_setup_platform enter")

    switch_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager.api.system_list:
        _LOGGER.info(f"async_setup_platform ventilation [{system.supports_ventilation()}]")
        if system.supports_ventilation():
            _LOGGER.info(f"Create S30 ventilation switch system [{system.sysId}]")
            switch = S30VentilationSwitch(hass, manager, system)
            switch_list.append(switch)
        if manager.allergenDefenderSwitch:
            _LOGGER.info(f"Create S30 allergenDefender switch system [{system.sysId}]")
            switch = S30AllergenDefenderSwitch(hass, manager, system)
            switch_list.append(switch)
        if system.numberOfZones > 1:
            _LOGGER.info(f"Create S30 zoning switch system [{system.sysId}]")
            switch = S30ZoningSwitch(hass, manager, system)
            switch_list.append(switch)

        ma_switch = S30ManualAwayModeSwitch(hass, manager, system)
        switch_list.append(ma_switch)
        _LOGGER.info(f"Create S30ManualAwayModeSwitch system [{system.sysId}]")
        sa_switch = S30SmartAwayEnableSwitch(hass, manager, system)
        switch_list.append(sa_switch)
        _LOGGER.info(f"Create S30SmartAwayEnableSwitch system [{system.sysId}]")

        if manager.create_equipment_parameters:
            par_safety_switch = S30ParameterSafetySwitch(hass, manager, system)
            switch_list.append(par_safety_switch)

    if len(switch_list) != 0:
        async_add_entities(switch_list, True)
        _LOGGER.debug(f"switch:async_setup_platform exit - created [{len(switch_list)}] switch entitites")
        return True
    else:
        _LOGGER.info("switch:async_setup_platform exit - no ventilators founds")
        return False


class S30VentilationSwitch(S30BaseEntityMixin, SwitchEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_ventilation"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "ventilationRemainingTime",
                "ventilatingUntilTime",
                "diagVentilationRuntime",
                "ventilationMode",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + "_VST").replace("-", "")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs: dict[str, Any] = {}
        attrs["ventilationRemainingTime"] = self._system.ventilationRemainingTime
        attrs["ventilatingUntilTime"] = self._system.ventilatingUntilTime
        attrs["diagVentilationRuntime"] = self._system.diagVentilationRuntime
        attrs["alwaysOn"] = self._system.ventilationMode == "on"
        attrs["timed"] = self._system.ventilationRemainingTime != 0
        return attrs

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.ventilationMode == "on" or self._system.ventilationRemainingTime > 0

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        equip_device_map = self._manager.system_equip_device_map.get(self._system.sysId)
        if equip_device_map is not None:
            device = equip_device_map.get(VENTILATION_EQUIPMENT_ID)
            if device is not None:
                return {
                    "identifiers": {(DOMAIN, device.unique_name)},
                }
            _LOGGER.warning("Unable to find VENTILATION_EQUIPMENT_ID in device map, please raise an issue")
        else:
            _LOGGER.error(
                f"No equipment device map found for sysId [{self._system.sysId}] equipment VENTILATION_EQUIPMENT_ID, please raise an issue"
            )
        return {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }

    async def async_turn_on(self, **kwargs):
        try:
            await self._system.ventilation_on()
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("ventilation_on:async_turn_on - error:" + e.message)
            else:
                _LOGGER.error("ventilation_on:async_turn_on - error:" + str(e))

    async def async_turn_off(self, **kwargs):
        try:
            _LOGGER.debug("ventilation:async_turn_off")
            called = False
            if self._system.ventilationMode == "on":
                _LOGGER.debug("ventilation:async_turn_off calling ventilation_off")
                await self._system.ventilation_off()
                called = True
            if self._system.ventilationRemainingTime > 0:
                await self._system.ventilation_timed(0)
                _LOGGER.debug("ventilation:async_turn_off calling ventilation_timed(0)")
                called = True
            if called:
                self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("ventilation_off:async_turn_off - error:" + e.message)
            else:
                _LOGGER.error("ventilation_off:async_turn_off - error:" + str(e))


class S30AllergenDefenderSwitch(S30BaseEntityMixin, SwitchEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_allergen_defender"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._system.registerOnUpdateCallback(self.update_callback, ["allergenDefender"])
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + "_ADST").replace("-", "")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {}

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.allergenDefender

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {"identifiers": {(DOMAIN, self._system.unique_id)}}

    async def async_turn_on(self, **kwargs):
        try:
            await self._system.allergenDefender_on()
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("allergenDefender_on:async_turn_on - error:" + e.message)
            else:
                _LOGGER.error("allergenDefender_on:async_turn_on - error:" + str(e))

    async def async_turn_off(self, **kwargs):
        try:
            await self._system.allergenDefender_off()
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("allergenDefender_off:async_turn_off - error:" + e.message)
            else:
                _LOGGER.error("allergenDefender_off:async_turn_off - error:" + str(e))


class S30ManualAwayModeSwitch(S30BaseEntityMixin, SwitchEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_manual_away_mode"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "manualAwayMode",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + "_SW_MA").replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.get_manual_away_mode()

    @property
    def device_info(self) -> DeviceInfo:
        return {"identifiers": {(DOMAIN, self._system.unique_id)}}

    async def async_turn_on(self, **kwargs):
        try:
            await self._system.set_manual_away_mode(True)
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("S30ManualAwayModeSwitch:async_turn_on - error:" + e.message)
            else:
                _LOGGER.error("S30ManualAwayModeSwitch:async_turn_on - error:" + str(e))

    async def async_turn_off(self, **kwargs):
        try:
            await self._system.set_manual_away_mode(False)
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("S30ManualAwayModeSwitch:async_turn_off - error:" + e.message)
            else:
                _LOGGER.error("S30ManualAwayModeSwitch:async_turn_off - error:" + str(e))


class S30SmartAwayEnableSwitch(S30BaseEntityMixin, SwitchEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_smart_away_enable"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "sa_enabled",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + "_SW_SAE").replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    def update(self):
        return True

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.sa_enabled

    @property
    def device_info(self) -> DeviceInfo:
        return {"identifiers": {(DOMAIN, self._system.unique_id)}}

    async def async_turn_on(self, **kwargs):
        try:
            await self._system.enable_smart_away(True)
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("S30SmartAwayEnableSwitch:async_turn_on - error:" + e.message)
            else:
                _LOGGER.error("S30SmartAwayEnableSwitch:async_turn_on - error:" + str(e))

    async def async_turn_off(self, **kwargs):
        try:
            await self._system.enable_smart_away(False)
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("S30SmartAwayEnableSwitch:async_turn_off - error:" + e.message)
            else:
                _LOGGER.error("S30SmartAwayEnableSwitch:async_turn_off - error:" + str(e))


class S30ZoningSwitch(S30BaseEntityMixin, SwitchEntity):
    """Class for iHarmony Zoning"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_zoning_enable"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "centralMode",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + "_SW_ZE").replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    def update(self):
        return True

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.centralMode is False

    @property
    def device_info(self) -> DeviceInfo:
        return {"identifiers": {(DOMAIN, self._system.unique_id)}}

    async def async_turn_on(self, **kwargs):
        try:
            await self._system.centralMode_off()
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("S30ZoningSwitch:async_turn_on - error:" + e.message)
            else:
                _LOGGER.error("S30ZoningSwitch:async_turn_on - error:" + str(e))

    async def async_turn_off(self, **kwargs):
        try:
            await self._system.centralMode_on()
            self._manager.mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("S30ZoningSwitch:async_turn_off - error:" + e.message)
            else:
                _LOGGER.error("S30ZoningSwitch:async_turn_off - error:" + str(e))


class S30ParameterSafetySwitch(S30BaseEntityMixin, SwitchEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
        rearm_duration_sec=60.0,
    ):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_parameter_safety"
        self._rearm_duration_sec = rearm_duration_sec
        manager.parameter_safety_turn_on(self._system.sysId)

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (f"{self._system.unique_id}{UNIQUE_ID_SUFFIX_PARAMETER_SAFETY_SWITCH}").replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    def update(self):
        return True

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        res = self._manager.parameter_safety_on(self._system.sysId)
        return res

    @property
    def device_info(self) -> DeviceInfo:
        return {"identifiers": {(DOMAIN, self._system.unique_id)}}

    async def async_turn_on(self, **kwargs):
        self._manager.parameter_safety_turn_on(self._system.sysId)
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        self._manager.parameter_safety_turn_off(self._system.sysId)
        asyncio.create_task(self.async_rearm_task())
        self.schedule_update_ha_state()

    async def async_rearm_task(self):
        await asyncio.sleep(self._rearm_duration_sec)
        self._manager.parameter_safety_turn_on(self._system.sysId)
        self.schedule_update_ha_state()

    @property
    def entity_category(self):
        return EntityCategory.CONFIG
