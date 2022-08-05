import logging
from . import Manager

from lennoxs30api import lennox_system

_LOGGER = logging.getLogger(__name__)


class S30BaseEntity(object):
    def __init__(self, manager: Manager, system: lennox_system):
        self._manager: Manager = manager
        self._system: lennox_system = system

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._manager.registerConnectionStateCallback(self.connection_state_callback)
        if self.base_ignore_cloud_status == False:
            self._system.registerOnUpdateCallback(
                self.cloud_status_update_callback,
                [
                    "cloud_status",
                ],
            )
        await super().async_added_to_hass()

    @property
    def base_ignore_cloud_status(self):
        return False

    def cloud_status_update_callback(self):
        _LOGGER.debug(
            f"cloud_status_update_callback cloud_status [{self._system.cloud_status}]"
        )
        self.schedule_update_ha_state()

    def connection_state_callback(self, connected: bool):
        _LOGGER.debug(f"connection_state_callback connected [{connected}]")
        self.schedule_update_ha_state()

    @property
    def available(self):
        if self._manager.connected == False:
            return False
        if (
            self.base_ignore_cloud_status == False
            and self._system.cloud_status == "offline"
        ):
            return False
        return super().available

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False
