"""Support for Lennoxs30 maintenance reminder sensors"""

# pylint: disable=line-too-long
# pylint: disable=invalid-name
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from lennoxs30api import lennox_system
from lennoxs30api.lennox_reminder import LennoxReminder

from . import Manager
from .base_entity import S30BaseEntityMixin
from .const import LENNOX_DOMAIN, UNIQUE_ID_SUFFIX_REMINDER

_LOGGER = logging.getLogger(__name__)


class S30ReminderSensor(S30BaseEntityMixin, SensorEntity):
    """Maintenance reminder (filter, UV bulb, humidifier pad, etc.), state is the percent remaining."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system, reminder: LennoxReminder):
        super().__init__(manager, system)
        self._hass = hass
        self._reminder: LennoxReminder = reminder
        self._myname = f"{self._system.name}_reminder_{reminder.kind}"
        # Only reminders configured on the thermostat are enabled by default
        self._attr_entity_registry_enabled_default = reminder.enabled is True

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("async_added_to_hass S30ReminderSensor myname [%s]", self._myname)
        self._reminder.register_on_update_callback(self.update_callback)
        await super().async_added_to_hass()

    def update_callback(self):
        """Callback to execute on data change"""
        _LOGGER.debug("update_callback S30ReminderSensor myname [%s]", self._myname)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        return (self._system.unique_id + UNIQUE_ID_SUFFIX_REMINDER + str(self._reminder.reminder_id)).replace("-", "")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs: dict[str, Any] = {}
        attrs["kind"] = self._reminder.kind
        attrs["enabled"] = self._reminder.enabled
        attrs["expired"] = self._reminder.expired
        attrs["expiry_type"] = self._reminder.expiry_type
        attrs["reminder_time"] = self._reminder.reminder_time
        attrs["set_time"] = self._reminder.set_time
        attrs["expiry_time"] = self._reminder.expiry_time
        attrs["expired_time"] = self._reminder.expired_time
        attrs["viewed"] = self._reminder.viewed
        return attrs

    @property
    def name(self):
        return self._myname

    @property
    def native_value(self):
        if self._reminder.enabled is not True or self._reminder.is_valid is not True:
            return None
        return self._reminder.remaining_pct

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(LENNOX_DOMAIN, self._system.unique_id)},
        }
