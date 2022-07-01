"""Support for Lennoxs30 outdoor temperature sensor"""
from typing import Any

from .base_entity import S30BaseEntity
from .const import (
    CONF_CLOUD_CONNECTION,
    MANAGER,
    UNIQUE_ID_SUFFIX_INTENET_STATUS_SENSOR,
    UNIQUE_ID_SUFFIX_RELAY_STATUS_SENSOR,
)
from . import Manager
from homeassistant.core import HomeAssistant
import logging
from lennoxs30api import lennox_system
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_PRESENCE,
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:

    sensor_list = []

    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager._api.getSystems():
        _LOGGER.info(
            f"Create S30HomeStateBinarySensor binary_sensor system [{system.sysId}]"
        )
        sensor = S30HomeStateBinarySensor(hass, manager, system)
        sensor_list.append(sensor)

        if entry.data[CONF_CLOUD_CONNECTION] == False:
            sensor = S30InternetStatus(hass, manager, system)
            sensor_list.append(sensor)
            sensor = S30RelayServerStatus(hass, manager, system)
            sensor_list.append(sensor)

    if len(sensor_list) != 0:
        async_add_entities(sensor_list, True)
        _LOGGER.debug(
            f"binary_sensor:async_setup_platform exit - created [{len(sensor_list)}] entitites"
        )
        return True
    else:
        _LOGGER.warning(
            f"binary_sensor:async_setup_platform exit - no S30HomeStateBinarySensor found - this should not happen"
        )
        return False


class S30HomeStateBinarySensor(S30BaseEntity, BinarySensorEntity):
    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager)
        self._hass = hass
        self._system = system
        self._myname = self._system.name + "_home_state"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass S30HomeStateBinarySensor myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "manualAwayMode",
                "sa_enabled",
                "sa_state",
                "sa_reset",
                "sa_cancel",
                "sa_setpointState",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(
            f"update_callback S30HomeStateBinarySensor myname [{self._myname}]"
        )
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_HS").replace("-", "")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs: dict[str, Any] = {}
        attrs["manual_away"] = self._system.get_manual_away_mode()
        attrs["smart_away"] = self._system.get_smart_away_mode()
        attrs["smart_away_enabled"] = self._system.sa_enabled
        attrs["smart_away_state"] = self._system.sa_state
        attrs["smart_away_reset"] = self._system.sa_reset
        attrs["smart_away_cancel"] = self._system.sa_cancel
        attrs["smart_away_setpoint_state"] = self._system.sa_setpointState
        return attrs

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.get_away_mode() == False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_PRESENCE


class S30InternetStatus(S30BaseEntity, BinarySensorEntity):
    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager)
        self._hass = hass
        self._system = system
        self._myname = self._system.name + "_internet_status"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(f"async_added_to_hass S30InternetStatus myname [{self._myname}]")
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "internetStatus",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(f"update_callback S30InternetStatus myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (
            self._system.unique_id() + UNIQUE_ID_SUFFIX_INTENET_STATUS_SENSOR
        ).replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def available(self):
        if self._system.internetStatus == None:
            return False
        return super().available

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.internetStatus == True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class S30RelayServerStatus(S30BaseEntity, BinarySensorEntity):
    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager)
        self._hass = hass
        self._system = system
        self._myname = self._system.name + "_relay_server"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass S30RelayServerStatus myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "relayServerConnected",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(f"update_callback S30RelayServerStatus myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (
            self._system.unique_id() + UNIQUE_ID_SUFFIX_RELAY_STATUS_SENSOR
        ).replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def name(self):
        return self._myname

    @property
    def available(self):
        if self._system.relayServerConnected == None:
            return False
        return super().available

    @property
    def is_on(self):
        return self._system.relayServerConnected == True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC
