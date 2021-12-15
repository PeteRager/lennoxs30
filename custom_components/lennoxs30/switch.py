"""Support for Lennoxs30 ventilation and allergend defender switches"""
from typing import Any
from config.custom_components.lennoxs30.const import MANAGER
from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_FAHRENHEIT, CONF_NAME
from . import Manager
from homeassistant.core import HomeAssistant
import logging
from homeassistant.helpers.entity import Entity
from lennoxs30api import lennox_system
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.switch import SwitchEntity, PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    _LOGGER.debug("switch:async_setup_platform enter")

    switch_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager._api.getSystems():
        _LOGGER.info(
            f"async_setup_platform ventilation [{system.supports_ventilation()}]"
        )
        if system.supports_ventilation():
            _LOGGER.info(f"Create S30 ventilation switch system [{system.sysId}]")
            switch = S30VentilationSwitch(hass, manager, system)
            switch_list.append(switch)
        if manager._allergenDefenderSwitch == True:
            _LOGGER.info(f"Create S30 allergenDefender switch system [{system.sysId}]")
            switch = S30AllergenDefenderSwitch(hass, manager, system)
            switch_list.append(switch)

    if len(switch_list) != 0:
        async_add_entities(switch_list, True)
        _LOGGER.debug(
            f"switch:async_setup_platform exit - created [{len(switch_list)}] switch entitites"
        )
        return True
    else:
        _LOGGER.info(f"switch:async_setup_platform exit - no ventilators founds")
        return False


class S30VentilationSwitch(SwitchEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "ventilationRemainingTime",
                "ventilatingUntilTime",
                "diagVentilationRuntime",
                "ventilationMode",
            ],
        )
        self._myname = self._system.name + "_ventilation"

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_VST").replace("-", "")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs: dict[str, Any] = {}
        attrs["ventilationRemainingTime"] = self._system.ventilationRemainingTime
        attrs["ventilatingUntilTime"] = self._system.ventilatingUntilTime
        attrs["diagVentilationRuntime"] = self._system.diagVentilationRuntime
        return attrs

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
        return self._system.ventilationMode == "on"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {"identifiers": {(DOMAIN, self._system.unique_id())}}

    async def async_turn_on(self, **kwargs):
        try:
            await self._system.ventilation_on()
            self._manager._mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("ventilation_on:async_turn_on - error:" + e.message)
            else:
                _LOGGER.error("ventilation_on:async_turn_on - error:" + str(e))

    async def async_turn_off(self, **kwargs):
        try:
            await self._system.ventilation_off()
            self._manager._mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("ventilation_off:async_turn_off - error:" + e.message)
            else:
                _LOGGER.error("ventilation_off:async_turn_off - error:" + str(e))


class S30AllergenDefenderSwitch(SwitchEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._system.registerOnUpdateCallback(
            self.update_callback, ["allergenDefender"]
        )
        self._myname = self._system.name + "_allergen_defender"

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_ADST").replace("-", "")

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
        return self._system.allergenDefender == True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {"identifiers": {(DOMAIN, self._system.unique_id())}}

    async def async_turn_on(self, **kwargs):
        try:
            await self._system.allergenDefender_on()
            self._manager._mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("allergenDefender_on:async_turn_on - error:" + e.message)
            else:
                _LOGGER.error("allergenDefender_on:async_turn_on - error:" + str(e))

    async def async_turn_off(self, **kwargs):
        try:
            await self._system.allergenDefender_off()
            self._manager._mp_wakeup_event.set()
        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error(
                    "allergenDefender_off:async_turn_off - error:" + e.message
                )
            else:
                _LOGGER.error("allergenDefender_off:async_turn_off - error:" + str(e))

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "name": self._system.name,
            "identifiers": {(DOMAIN, self._system.unique_id())},
            "manufacturer": "Lennox",
            "model": "Lennox S30",
        }
