import logging
from . import Manager

_LOGGER = logging.getLogger(__name__)


class S30BaseEntity(object):
    def __init__(self, manager: Manager):
        self._manager: Manager = manager

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._manager.registerConnectionStateCallback(self.connection_state_callback)
        await super().async_added_to_hass()

    def connection_state_callback(self, connected: bool):
        _LOGGER.debug(f"connection_state_callback connected [{connected}]")
        self.schedule_update_ha_state()

    @property
    def available(self):
        if self._manager.connected == False:
            return False
        return super().available

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False
