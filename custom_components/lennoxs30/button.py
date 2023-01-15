"""Support for Lennoxs30 outdoor temperature sensor"""
# pylint: disable=global-statement
# pylint: disable=broad-except
# pylint: disable=unused-argument
# pylint: disable=line-too-long
# pylint: disable=invalid-name

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import lennox_system
from lennoxs30api.s30exception import S30Exception

from .base_entity import S30BaseEntityMixin
from .const import (
    LOG_INFO_BUTTON_PRESS,
    MANAGER,
    UNIQUE_ID_SUFFIX_PARAMETER_UPDATE_BUTTON,
    UNIQUE_ID_SUFFIX_RESET_SMART_HUB,
)
from .helpers import helper_create_system_unique_id, helper_get_equipment_device_info
from . import DOMAIN, Manager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup the button entities"""
    _LOGGER.debug("buttomn:async_setup_platform enter")

    button_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager.api.system_list:
        if manager.create_equipment_parameters:
            button = EquipmentParameterUpdateButton(hass, manager, system)
            button_list.append(button)
            button_list.append(ResetSmartHubButton(hass, manager, system))

    if len(button_list) != 0:
        async_add_entities(button_list, True)


class EquipmentParameterUpdateButton(S30BaseEntityMixin, ButtonEntity):
    """Set the humidity mode"""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
    ):
        super().__init__(manager, system)
        self.hass: HomeAssistant = hass
        self._myname = self._system.name + "_parameter_update"
        _LOGGER.debug("Create EquipmentParameterUpdateButton myname [%s]", self._myname)

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id + UNIQUE_ID_SUFFIX_PARAMETER_UPDATE_BUTTON).replace("-", "")

    @property
    def name(self):
        return self._myname

    async def async_press(self) -> None:
        """Update the current value."""
        _LOGGER.info(LOG_INFO_BUTTON_PRESS, self.__class__.__name__, self._myname)
        if self._manager.parameter_safety_on(self._system.sysId):
            raise HomeAssistantError(f"Unable to parameter update [{self._myname}] parameter safety switch is on")
        try:
            await self._system.set_parameter_value(0, 0, "")
        except S30Exception as ex:
            raise HomeAssistantError(f"Unable to parameter update [{self._myname}] [{ex.as_string()}]") from ex
        except Exception as ex:
            raise HomeAssistantError(
                f"EquipmentParameterUpdateButton::async_press unexpected exception, please log issue, [{self._myname}] exception [{ex}]"
            ) from ex

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return helper_get_equipment_device_info(self._manager, self._system, 0)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG


class ResetSmartHubButton(S30BaseEntityMixin, ButtonEntity):
    """Reset the LCC"""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
    ):
        super().__init__(manager, system)
        self.hass: HomeAssistant = hass
        self._myname = self._system.name + "_reset_smarthub"
        _LOGGER.debug("Create ResetSmartHubButton myname [%s]", self._myname)

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return helper_create_system_unique_id(self._system, UNIQUE_ID_SUFFIX_RESET_SMART_HUB)

    @property
    def name(self):
        return self._myname

    async def async_press(self) -> None:
        """Update the current value."""
        _LOGGER.info(LOG_INFO_BUTTON_PRESS, self.__class__.__name__, self._myname)

        if self._manager.parameter_safety_on(self._system.sysId):
            raise HomeAssistantError(f"Unable to reset controller [{self._myname}] parameter safety switch is on")

        try:
            await self._system.reset_smart_controller()
        except S30Exception as ex:
            raise HomeAssistantError(f"Unable ResetSmartHub [{self._myname}] [{ex.as_string()}]") from ex
        except Exception as ex:
            raise HomeAssistantError(
                f"ResetSmartHubButton::async_press unexpected exception, please log issue, [{self._myname}] exception [{ex}]"
            ) from ex

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return helper_get_equipment_device_info(self._manager, self._system, 0)

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC
