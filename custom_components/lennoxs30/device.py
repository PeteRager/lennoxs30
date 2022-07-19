from lennoxs30api.s30api_async import lennox_system, lennox_zone, lennox_equipment
from .const import LENNOX_DOMAIN, LENNOX_MFG
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr


class Device(object):
    def __init__(self, eq: lennox_equipment):
        self.eq: lennox_equipment = eq

    @property
    def hw_version(self):
        if self.eq != None:
            return self.eq.unit_serial_number
        return None

    @property
    def unique_name(self) -> str:
        raise NotImplemented


class S30ControllerDevice(Device):
    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, system: lennox_system
    ):
        super().__init__(system.equipment.get(0))
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
            suggested_area="basement",
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
        super().__init__(system.get_outdoor_unit_equipment())
        self._hass = hass
        self._system = system
        self._config_entry = config_entry
        self._s30_controller_device: S30ControllerDevice = s30_device

    @property
    def unique_name(self) -> str:
        return self._system.unique_id() + "_ou"

    @property
    def device_model(self):
        if self.eq != None:
            return self.eq.unit_model_number
        return self._system.outdoorUnitType

    def register_device(self):
        device_registry = dr.async_get(self._hass)
        if self.eq != None and self.eq.equipment_type_name != None:
            name = f"{self._system.name} {self.eq.equipment_type_name}"
        elif self._system.outdoorUnitType != None:
            name = f"{self._system.name} {self._system.outdoorUnitType}"
        else:
            name = f"{self._system.name} outdoor unit"

        device_registry.async_get_or_create(
            config_entry_id=self._config_entry.entry_id,
            identifiers={(LENNOX_DOMAIN, self.unique_name)},
            manufacturer=LENNOX_MFG,
            suggested_area="outside",
            name=name,
            model=self.device_model,
            hw_version=self.hw_version,
            via_device=(LENNOX_DOMAIN, self._s30_controller_device.unique_name),
        )


class S30IndoorUnit(Device):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        system: lennox_system,
        s30_device: S30ControllerDevice,
    ):
        super().__init__(system.get_indoor_unit_equipment())
        self._hass = hass
        self._system = system
        self._config_entry = config_entry
        self._s30_controller_device: S30ControllerDevice = s30_device

    @property
    def unique_name(self) -> str:
        return self._system.unique_id() + "_iu"

    @property
    def device_model(self):
        if self.eq != None:
            return self.eq.unit_model_number
        return self._system.indoorUnitType

    def register_device(self):
        device_registry = dr.async_get(self._hass)
        if self.eq != None and self.eq.equipment_type_name != None:
            name = f"{self._system.name} {self.eq.equipment_type_name}"
        elif self._system.indoorUnitType != None:
            name = f"{self._system.name} {self._system.indoorUnitType}"
        else:
            name = f"{self._system.name} indoor unit"

        device_registry.async_get_or_create(
            config_entry_id=self._config_entry.entry_id,
            identifiers={(LENNOX_DOMAIN, self.unique_name)},
            manufacturer=LENNOX_MFG,
            suggested_area="basement",
            name=name,
            model=self.device_model,
            hw_version=self.hw_version,
            via_device=(LENNOX_DOMAIN, self._s30_controller_device.unique_name),
        )


class S30AuxiliaryUnit(Device):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        system: lennox_system,
        s30_device: S30ControllerDevice,
        equipment: lennox_equipment,
    ):
        super().__init__(equipment)
        self._hass = hass
        self._system = system
        self._config_entry = config_entry
        self._s30_controller_device: S30ControllerDevice = s30_device

    @property
    def unique_name(self) -> str:
        # Not sure if every device has a serial number.
        if self.eq.unit_serial_number == None:
            suffix = self.eq.equipment_id
        else:
            suffix = self.eq.unit_serial_number
        return f"{self._system.unique_id()}_{suffix}"

    @property
    def device_model(self):
        if self.eq != None:
            return self.eq.unit_model_number
        return None

    def register_device(self):
        device_registry = dr.async_get(self._hass)
        name = f"{self._system.name} {self.eq.equipment_type_name}"

        device_registry.async_get_or_create(
            config_entry_id=self._config_entry.entry_id,
            identifiers={(LENNOX_DOMAIN, self.unique_name)},
            manufacturer=LENNOX_MFG,
            suggested_area="basement",
            name=name,
            model=self.device_model,
            hw_version=self.hw_version,
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
