"""Support for Lennoxs30 outdoor temperature sensor"""
from lennoxs30api.s30exception import S30Exception
from .const import MANAGER
from homeassistant.components.select import SelectEntity
from . import DOMAIN, Manager
from homeassistant.core import HomeAssistant
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from lennoxs30api.s30api_async import (
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    lennox_system,
    lennox_zone,
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
        for zone in system.getZones():
            if zone.is_zone_active() == True:
                if (
                    zone.dehumidificationOption == True
                    or zone.humidificationOption == True
                ):
                    _LOGGER.debug(
                        f"Create HumiditySelect [{system.sysId}] zone [{zone.name}] "
                    )
                climate = HumidityModeSelect(hass, manager, system, zone)
                select_list.append(climate)

    if len(select_list) != 0:
        async_add_entities(select_list, True)


class HumidityModeSelect(SelectEntity):
    """Set the diagnostic level in the S30."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
        zone: lennox_zone,
    ):
        self.hass: HomeAssistant = hass
        self._manager: Manager = manager
        self._system = system
        self._zone = zone
        self._zone.registerOnUpdateCallback(self.zone_update_callback)
        self._myname = self._system.name + "_" + self._zone.name + "_humidity_mode"
        self._currentOption = self._zone.humidityMode
        _LOGGER.debug(f"Create HumidityModeSelect myname [{self._myname}]")

    def zone_update_callback(self):
        _LOGGER.debug(
            f"update_callback HumidityModeSelect myname [{self._myname}] current_hvac_mode [{self._currentOption}] updated_hvac_mode [{self._zone.humidityMode}]"
        )
        if self._currentOption != self._zone.humidityMode:
            _LOGGER.debug(
                f"update_callback DiagnosticLevelNumber myname [{self._myname}]"
            )
            self._currentOption = self._zone.humidityMode
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
        return self._currentOption

    @property
    def options(self) -> list:
        list = []
        if self._zone.dehumidificationOption == True:
            list.append(LENNOX_HUMIDITY_MODE_DEHUMIDIFY)
        if self._zone.humidificationOption == True:
            list.append(LENNOX_HUMIDITY_MODE_HUMIDIFY)
        list.append(LENNOX_HUMIDITY_MODE_OFF)
        return list

    async def async_select_option(self, option: str) -> None:
        try:
            await self._zone.setHumidityMode(str)
        except S30Exception as e:
            _LOGGER.error("async_select_option " + e.as_string())
        except Exception as e:
            _LOGGER.exception("async_select_option")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
        }
        return result
