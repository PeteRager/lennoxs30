"""Support for Lennoxs30 outdoor temperature sensor"""
# pylint: disable=global-statement
# pylint: disable=broad-except
# pylint: disable=unused-argument
# pylint: disable=line-too-long

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY, BinarySensorEntity
from lennoxs30api import lennox_system, LennoxBle, LENNOX_BLE_COMMSTATUS_AVAILABLE

from .base_entity import S30BaseEntityMixin
from .device import helper_create_ble_device_id
from .const import UNIQUE_ID_SUFFIX_BLE_COMMSTATUS
from .helpers import helper_create_system_unique_id
from . import Manager

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


class BleCommStatusBinarySensor(S30BaseEntityMixin, BinarySensorEntity):
    """Entity for S30 connected to internet"""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system, ble_device: LennoxBle):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = f"{self._system.name}_{ble_device.deviceName}_comm_status"
        self._ble_device: LennoxBle = ble_device

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass BleCommStatusBinarySensor myname [%s]", self._myname)
        self._ble_device.register_on_update_callback(
            self.update_callback,
            [
                "commStatus",
            ],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        """Callback for data change"""
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("update_callback S40BleCommStatusBinarySensor myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        return helper_create_system_unique_id(
            self._system, f"{UNIQUE_ID_SUFFIX_BLE_COMMSTATUS}_{self._ble_device.ble_id}"
        )

    @property
    def extra_state_attributes(self):
        return {"commStatus": self._ble_device.commStatus}

    @property
    def name(self):
        return self._myname

    @property
    def is_on(self):
        return self._ble_device.commStatus == LENNOX_BLE_COMMSTATUS_AVAILABLE

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, helper_create_ble_device_id(self._system, self._ble_device))},
        }

    @property
    def device_class(self):
        return DEVICE_CLASS_CONNECTIVITY

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC
