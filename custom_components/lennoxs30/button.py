"""Support for Lennoxs30 outdoor temperature sensor"""

from lennoxs30api.s30exception import S30Exception

from custom_components.lennoxs30.helpers import helper_get_equipment_device_info

from .base_entity import S30BaseEntityMixin
from .const import MANAGER, UNIQUE_ID_SUFFIX_PARAMETER_UPDATE_BUTTON
from homeassistant.components.button import ButtonEntity
from . import DOMAIN, Manager
from homeassistant.core import HomeAssistant
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import lennox_system


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    _LOGGER.debug("buttomn:async_setup_platform enter")

    button_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager.api.getSystems():
        if manager._create_equipment_parameters:
            button = EquipmentParameterUpdateButton(hass, manager, system)
            button_list.append(button)

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
        _LOGGER.debug(f"Create EquipmentParameterUpdateButton myname [{self._myname}]")

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + UNIQUE_ID_SUFFIX_PARAMETER_UPDATE_BUTTON).replace("-", "")

    @property
    def name(self):
        return self._myname

    async def async_press(self) -> None:
        """Update the current value."""
        _LOGGER.info(f"EquipmentParameterUpdateButton::async_press [{self._myname}]")

        if self._manager.parameter_safety_on(self._system.sysId):
            raise HomeAssistantError(f"Unable to parameter update [{self._myname}] parameter safety switch is on")

        try:
            await self._system._internal_set_equipment_parameter_value(0, 0, "")
        except S30Exception as e:
            _LOGGER.error(
                f"EquipmentParameterUpdateButton::async_press S30Exception [{self._myname}] [{e.as_string()}]"
            )
        except Exception as e:
            _LOGGER.exception(
                f"EquipmentParameterUpdateButton::async_press unexpected exception, please log issue, [{self._myname}] exception [{e}]"
            )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return helper_get_equipment_device_info(self._manager, self._system, 0)

    @property
    def entity_category(self):
        return EntityCategory.CONFIG
