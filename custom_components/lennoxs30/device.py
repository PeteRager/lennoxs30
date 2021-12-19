from lennoxs30api.s30api_async import lennox_system, lennox_zone, s30api_async
from .const import LENNOX_DOMAIN, LENNOX_MFG
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr


class Device(object):
    pass


class S30ControllerDevice(Device):
    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, system: lennox_system
    ):
        self._hass = hass
        self._system = system
        self._config_entry = config_entry

    @property
    def unique_name(self) -> str:
        return self._system.unique_id()

    def register_device(self):
        device_registry = dr.async_get(self._hass)

        device_registry.async_get_or_create(
            config_entry_id=self._config_entry.entry_id,
            #            connections={(dr.CONNECTION_NETWORK_MAC, config.mac)},
            identifiers={(LENNOX_DOMAIN, self.unique_name)},
            manufacturer=LENNOX_MFG,
            suggested_area="Basement",
            name=self._system.name,
            model=self._system.productType,
            sw_version=self._system.softwareVersion,
        )


class S30OutdoorUnit(Device):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        system: lennox_system,
        s30_device: S30ControllerDevice,
    ):
        self._hass = hass
        self._system = system
        self._config_entry = config_entry
        self._s30_controller_device: S30ControllerDevice = s30_device

    @property
    def unique_name(self) -> str:
        return self._system.unique_id() + "_ou"

    def register_device(self):
        device_registry = dr.async_get(self._hass)

        device_registry.async_get_or_create(
            config_entry_id=self._config_entry.entry_id,
            identifiers={(LENNOX_DOMAIN, self.unique_name)},
            manufacturer=LENNOX_MFG,
            suggested_area="Outside",
            name=self._system.name + " outdoor unit",
            model=self._system.outdoorUnitType,
            via_device=(LENNOX_DOMAIN, self._s30_controller_device.unique_name),
        )


class S30ZoneThermostat(Device):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        system: lennox_system,
        zone: lennox_zone,
        s30_device: S30ControllerDevice,
    ):
        self._hass = hass
        self._system = system
        self._zone = zone
        self._config_entry = config_entry
        self._s30_controller_device: S30ControllerDevice = s30_device

    @property
    def unique_name(self) -> str:
        return self._zone.unique_id

    def register_device(self):
        device_registry = dr.async_get(self._hass)

        device_registry.async_get_or_create(
            config_entry_id=self._config_entry.entry_id,
            identifiers={(LENNOX_DOMAIN, self.unique_name)},
            manufacturer=LENNOX_MFG,
            name=self._system.name + "_" + self._zone.name,
            model="thermostat",
            via_device=(LENNOX_DOMAIN, self._s30_controller_device.unique_name),
        )
