"""Support for Lennoxs30 outdoor temperature sensor"""
# pylint: disable=global-statement
# pylint: disable=broad-except
# pylint: disable=unused-argument
# pylint: disable=line-too-long

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_PRESENCE,
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)

from lennoxs30api import lennox_system, LENNOX_OUTDOOR_UNIT_HP


from .base_entity import S30BaseEntityMixin
from .const import (
    MANAGER,
    UNIQUE_ID_SUFFIX_AUX_HI_AMBIENT_LOCKOUT,
    UNIQUE_ID_SUFFIX_CLOUD_CONNECTED_SENSOR,
    UNIQUE_ID_SUFFIX_HP_LOW_AMBIENT_LOCKOUT,
    UNIQUE_ID_SUFFIX_INTENET_STATUS_SENSOR,
    UNIQUE_ID_SUFFIX_RELAY_STATUS_SENSOR,
)
from . import Manager

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up the binary entities"""
    sensor_list = []

    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager.api.system_list:
        _LOGGER.debug("Create S30HomeStateBinarySensor binary_sensor system [%s]", system.sysId)
        sensor = S30HomeStateBinarySensor(hass, manager, system)
        sensor_list.append(sensor)

        if manager.api.isLANConnection:
            sensor = S30InternetStatus(hass, manager, system)
            sensor_list.append(sensor)
            sensor = S30RelayServerStatus(hass, manager, system)
            sensor_list.append(sensor)
        else:
            sensor = S30CloudConnectedStatus(hass, manager, system)
            sensor_list.append(sensor)

        if system.outdoorUnitType == LENNOX_OUTDOOR_UNIT_HP:
            sensor_list.append(S30HeatpumpLowAmbientLockout(hass, manager, system))
            sensor_list.append(S30AuxheatHighAmbientLockout(hass, manager, system))

    if len(sensor_list) != 0:
        async_add_entities(sensor_list, True)
        _LOGGER.debug("binary_sensor:async_setup_platform exit - created [%d] entitites", len(sensor_list))
        return True
    else:
        _LOGGER.warning(
            "binary_sensor:async_setup_platform exit - no S30HomeStateBinarySensor found - this should not happen"
        )
        return False


class S30HomeStateBinarySensor(S30BaseEntityMixin, BinarySensorEntity):
    """Home State Binary Sensor"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_home_state"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass S30HomeStateBinarySensor myname [%s]", self._myname)
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
        """Callback for data change"""
        _LOGGER.debug("update_callback S30HomeStateBinarySensor myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + "_HS").replace("-", "")

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
        return self._system.get_away_mode() is False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_PRESENCE


class S30InternetStatus(S30BaseEntityMixin, BinarySensorEntity):
    """Entity for S30 connected to internet"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_internet_status"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass S30InternetStatus myname [%s]", self._myname)
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "internetStatus",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        """Callback for data change"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("update_callback S30InternetStatus myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + UNIQUE_ID_SUFFIX_INTENET_STATUS_SENSOR).replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def available(self):
        if self._system.internetStatus is None:
            return False
        return super().available

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.internetStatus

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class S30RelayServerStatus(S30BaseEntityMixin, BinarySensorEntity):
    """Relay Server Status"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_relay_server"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass S30RelayServerStatus myname [%s]", self._myname)
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "relayServerConnected",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        """Callback for data change"""
        _LOGGER.debug("update_callback S30RelayServerStatus myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + UNIQUE_ID_SUFFIX_RELAY_STATUS_SENSOR).replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def name(self):
        return self._myname

    @property
    def available(self):
        if self._system.relayServerConnected is None:
            return False
        return super().available

    @property
    def is_on(self):
        return self._system.relayServerConnected

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class S30CloudConnectedStatus(S30BaseEntityMixin, BinarySensorEntity):
    """Cloud connection status"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_cloud_connected"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass S30CloudConnectedStatus myname [%s]", self._myname)
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "cloud_status",
            ],
        )
        await super().async_added_to_hass()

    @property
    def base_ignore_cloud_status(self):
        return True

    def update_callback(self):
        """Callback for data change"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("update_callback S30CloudConnectedStatus myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + UNIQUE_ID_SUFFIX_CLOUD_CONNECTED_SENSOR).replace("-", "")

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def name(self):
        return self._myname

    @property
    def available(self):
        if self._system.cloud_status is None:
            return False
        return super().available

    @property
    def is_on(self):
        if self._system.cloud_status == "online":
            return True
        elif self._system.cloud_status == "offline":
            return False
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class S30HeatpumpLowAmbientLockout(S30BaseEntityMixin, BinarySensorEntity):
    """Heatpump is locked out"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_hp_lo_ambient_lockout"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass S30HeatpumpLowAmbientLockout myname [%s]", self._myname)
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "heatpump_low_ambient_lockout",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        """Callback for data change"""
        _LOGGER.debug("update_callback S30HeatpumpLowAmbientLockout myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + UNIQUE_ID_SUFFIX_HP_LOW_AMBIENT_LOCKOUT).replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.heatpump_low_ambient_lockout

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }


class S30AuxheatHighAmbientLockout(S30BaseEntityMixin, BinarySensorEntity):
    """Auxheat lockout"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_auxheat_hi_ambient_lockout"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass S30AuxheatHighAmbientLockout myname [%s]", self._myname)
        self._system.registerOnUpdateCallback(
            self.update_callback,
            [
                "aux_heat_high_ambient_lockout",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        """Callback for data change"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("update_callback S30AuxheatHighAmbientLockout myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + UNIQUE_ID_SUFFIX_AUX_HI_AMBIENT_LOCKOUT).replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._system.aux_heat_high_ambient_lockout

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id)},
        }
