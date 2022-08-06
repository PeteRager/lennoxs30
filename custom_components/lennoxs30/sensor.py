"""Support for Lennoxs30 outdoor temperature sensor"""
from .device import Device
from .base_entity import S30BaseEntity
from .const import MANAGER, UNIQUE_ID_SUFFIX_DIAG_SENSOR
from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    FREQUENCY_HERTZ,
    ELECTRIC_CURRENT_AMPERE,
    VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE,
    ELECTRIC_POTENTIAL_VOLT,
    TIME_MINUTES,
    TIME_SECONDS,
)
from . import Manager
from homeassistant.core import HomeAssistant
import logging
from lennoxs30api import (
    lennox_system,
    lennox_zone,
    lennox_equipment,
    lennox_equipment_diagnostic,
    LENNOX_STATUS_NOT_AVAILABLE,
    LENNOX_STATUS_NOT_EXIST,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from homeassistant.components.sensor import (
    SensorStateClass,
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
    SensorDeviceClass,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:

    sensor_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager._api.getSystems():
        if system.outdoorTemperatureStatus != LENNOX_STATUS_NOT_EXIST:
            _LOGGER.info(f"Create S30OutdoorTempSensor system [{system.sysId}]")
            sensor = S30OutdoorTempSensor(hass, manager, system)
            sensor_list.append(sensor)
        else:
            _LOGGER.info(
                f"Not creating S30OutdoorTempSensor system [{system.sysId}] - sensor does not exist"
            )

        if manager._create_inverter_power == True:
            _LOGGER.info(f"Create S30InverterPowerSensor system [{system.sysId}]")
            if system.diagLevel != 2:
                _LOGGER.warning(
                    f"Power Inverter Sensor requires S30 to be in diagLevel 2, currently in [{system.diagLevel}]"
                )
            if system.internetStatus == True or system.relayServerConnected == True:
                _LOGGER.warning(
                    f"To prevent S30 instability - Power Inverter Sensor requires S30 to be isolated from internet - internetStatus [{system.internetStatus}] relayServerConnected [{system.relayServerConnected}] - https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md"
                )
            power_sensor = S30InverterPowerSensor(hass, manager, system)
            sensor_list.append(power_sensor)

        if manager._create_diagnostic_sensors == True:
            _LOGGER.info(f"Create Diagnostic Sensors system [{system.sysId}]")
            if system.diagLevel != 2:
                _LOGGER.warning(
                    f"Diagnostics requires S30 to be in diagLevel 2, currently in [{system.diagLevel}]"
                )
            if system.internetStatus == True or system.relayServerConnected == True:
                _LOGGER.warning(
                    f"To prevent S30 instability - diagnostics requires S30 to be isolated from internet - internetStatus [{system.internetStatus}] relayServerConnected [{system.relayServerConnected}] - https://github.com/PeteRager/lennoxs30/blob/master/docs/diagnostics.md"
                )
            for e_id, eq in system.equipment.items():
                equip: lennox_equipment = eq
                if equip.equipment_id != 0:
                    for did, diagnostic in equip.diagnostics.items():
                        if diagnostic.valid == True:
                            _LOGGER.info(
                                f"Create Diagsensor system [{system.sysId}] eid [{equip.equipment_id}] did [{diagnostic.diagnostic_id}] name [{diagnostic.name}]"
                            )
                            diagsensor = S30DiagSensor(
                                hass, manager, system, equip, diagnostic
                            )
                            sensor_list.append(diagsensor)

        if manager._createSensors == True:
            for zone in system.getZoneList():
                if zone.is_zone_active() == True:
                    _LOGGER.info(
                        f"Create S30TempSensor sensor system [{system.sysId}] zone [{zone.id}]"
                    )
                    tempSensor = S30TempSensor(hass, manager, system, zone)
                    sensor_list.append(tempSensor)
                    _LOGGER.info(
                        f"Create S30HumSensor sensor system [{system.sysId}] zone [{zone.id}]"
                    )
                    humSensor = S30HumiditySensor(hass, manager, system, zone)
                    sensor_list.append(humSensor)

    if len(sensor_list) != 0:
        async_add_entities(sensor_list, True)
        _LOGGER.debug(
            f"sensor:async_setup_platform exit - created [{len(sensor_list)}] entitites"
        )
        return True
    else:
        _LOGGER.info(
            f"sensor:async_setup_platform exit - no system outdoor temperatures found"
        )
        return False


class S30DiagSensor(S30BaseEntity, SensorEntity):
    def __init__(
        self,
        hass,
        manager: Manager,
        system: lennox_system,
        equipment: lennox_equipment,
        diagnostic: lennox_equipment_diagnostic,
    ):
        super().__init__(manager, system)
        self._hass = hass
        self._equipment: lennox_equipment = equipment
        self._diagnostic: lennox_equipment_diagnostic = diagnostic

        suffix = str(self._equipment.equipment_id)
        if self._equipment.equipment_id == 1:
            suffix = "ou"
        elif self._equipment.equipment_id == 2:
            suffix = "iu"
        self._myname = f"{self._system.name}_{suffix}_{self._diagnostic.name}".replace(
            " ", "_"
        )
        _LOGGER.debug(f"Create S30DiagSensor myname [{self._myname}]")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(f"async_added_to_hass S30DiagSensor myname [{self._myname}]")
        self._system.registerOnUpdateCallbackDiag(
            self.update_callback,
            [f"{self._equipment.equipment_id}_{self._diagnostic.diagnostic_id}"],
        )
        self._system.registerOnUpdateCallback(
            self.system_update_callback, ["diagLevel"]
        )
        await super().async_added_to_hass()

    def update_callback(self, eid_did, newval):
        _LOGGER.debug(
            f"update_callback S30DiagSSensor myname [{self._myname}] value {newval}"
        )
        self.schedule_update_ha_state()

    def system_update_callback(self):
        _LOGGER.debug(f"system_update_callback S30DiagSSensor myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def available(self) -> bool:
        if self._system.diagLevel not in (1, 2):
            return False
        return super().available

    @property
    def native_value(self):
        """Return native value of the sensor."""
        if self._diagnostic.value == "waiting...":
            return None
        return self._diagnostic.value

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {}

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (
            f"{self._system.unique_id()}_{UNIQUE_ID_SUFFIX_DIAG_SENSOR}_{self._equipment.equipment_id}_{self._diagnostic.name}"
        ).replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def native_unit_of_measurement(self):
        unit = self._diagnostic.unit

        if unit == "F":
            return TEMP_FAHRENHEIT
        if unit == "C":
            return TEMP_CELSIUS  ## Not validated - do no know if European Units report
        if unit == "CFM":
            return VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE
        if unit == "min":
            return TIME_MINUTES
        if unit == "sec":
            return TIME_SECONDS
        if unit == "%":
            return PERCENTAGE
        if unit == "Hz":
            return FREQUENCY_HERTZ
        if unit == "V":
            return ELECTRIC_POTENTIAL_VOLT
        if unit == "A":
            return ELECTRIC_CURRENT_AMPERE
        if unit == "":
            return None
        return unit

    @property
    def device_class(self):
        uom = self.native_unit_of_measurement
        if uom == TEMP_FAHRENHEIT:
            return SensorDeviceClass.TEMPERATURE
        elif uom == TEMP_CELSIUS:
            return SensorDeviceClass.TEMPERATURE
        elif uom == ELECTRIC_POTENTIAL_VOLT:
            return SensorDeviceClass.VOLTAGE
        elif uom == ELECTRIC_CURRENT_AMPERE:
            return SensorDeviceClass.CURRENT
        elif uom == FREQUENCY_HERTZ:
            return SensorDeviceClass.FREQUENCY
        return None

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        equip_device_map = self._manager.system_equip_device_map.get(self._system.sysId)
        if equip_device_map != None:
            device = equip_device_map.get(self._equipment.equipment_id)
            if device != None:
                return {
                    "identifiers": {(DOMAIN, device.unique_name)},
                }
            _LOGGER.warning(
                f"Unable to find equipment in device map [{self._equipment.equipment_id}] [{self._equipment.equipment_name}] [{self._equipment.equipment_type_name}] [{self._equipment.equipType}], please raise an issue and post a message log"
            )
        else:
            _LOGGER.error(
                f"No equipment device map found for sysId [{self._system.sysId}] equipment [{self._equipment.equipment_id}] [{self._equipment.equipment_name}] [{self._equipment.equipment_type_name}] [{self._equipment.equipType}], please raise an issue and post a message log"
            )
        return {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class S30OutdoorTempSensor(S30BaseEntity, SensorEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_outdoor_temperature"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            f"async_added_to_hass S30OutdoorTempSensor myname [{self._myname}]"
        )
        self._system.registerOnUpdateCallback(
            self.update_callback,
            ["outdoorTemperature", "outdoorTemperatureC", "outdoorTemperatureStatus"],
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(f"update_callback S30OutdoorTempSensor myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_OT").replace("-", "")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {}

    @property
    def name(self):
        return self._myname

    @property
    def native_value(self):
        if (
            self._system.outdoorTemperatureStatus == LENNOX_STATUS_NOT_EXIST
            or self._system.outdoorTemperatureStatus == LENNOX_STATUS_NOT_AVAILABLE
        ):
            _LOGGER.warning(
                f"S30OutdoorTempSensor [{self._myname}] has bad data quality [{self._system.outdoorTemperatureStatus}] returning None "
            )
            return None
        if self._manager._is_metric is False:
            return self._system.outdoorTemperature
        return self._system.outdoorTemperatureC

    @property
    def native_unit_of_measurement(self):
        if self._manager._is_metric is False:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id() + "_ou")},
        }


class S30TempSensor(S30BaseEntity, SensorEntity):
    """Class for Lennox S30 thermostat temperature."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
        zone: lennox_zone,
    ):
        super().__init__(manager, system)
        self._hass = hass
        self._zone = zone
        self._myname = self._zone._system.name + "_" + self._zone.name + "_temperature"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(f"async_added_to_hass S30TempSensor myname [{self._myname}]")
        self._zone.registerOnUpdateCallback(
            self.update_callback, ["temperature", "temperatureC"]
        )
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(f"update_callback S30TempSensor myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._zone._system.unique_id() + "_" + str(self._zone.id)).replace(
            "-", ""
        ) + "_T"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {}

    @property
    def name(self):
        return self._myname

    @property
    def native_value(self):
        if self._manager._is_metric is False:
            return self._zone.getTemperature()
        return self._zone.getTemperatureC()

    @property
    def native_unit_of_measurement(self):
        if self._manager._is_metric is False:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
        }


class S30HumiditySensor(S30BaseEntity, SensorEntity):
    """Class for Lennox S30 thermostat temperature."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: Manager,
        system: lennox_system,
        zone: lennox_zone,
    ):
        super().__init__(manager, system)
        self._hass = hass
        self._zone = zone
        self._myname = self._zone._system.name + "_" + self._zone.name + "_humidity"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(f"async_added_to_hass S30TempSensor myname [{self._myname}]")
        self._zone.registerOnUpdateCallback(self.update_callback, ["humidity"])
        await super().async_added_to_hass()

    def update_callback(self):
        _LOGGER.debug(f"update_callback S30HumiditySensor myname [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._zone._system.unique_id() + "_" + str(self._zone.id)).replace(
            "-", ""
        ) + "_H"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {}

    @property
    def name(self):
        return self._myname

    @property
    def native_value(self):
        return self._zone.getHumidity()

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    @property
    def device_class(self):
        return SensorDeviceClass.HUMIDITY

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
        }


class S30InverterPowerSensor(S30BaseEntity, SensorEntity):
    """Class for Lennox S30 inverter power."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        super().__init__(manager, system)
        self._hass = hass
        self._myname = self._system.name + "_inverter_energy"

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(f"async_added_to_hass S30TempSensor myname [{self._myname}]")
        self._system.registerOnUpdateCallback(
            self.update_callback,
            ["diagInverterInputVoltage", "diagInverterInputCurrent"],
        )
        self._system.registerOnUpdateCallback(
            self.system_update_callback, ["diagLevel"]
        )
        await super().async_added_to_hass()

    def system_update_callback(self):
        _LOGGER.debug(
            f"system_update_callback S30InverterPowerSensor myname [{self._myname}]"
        )
        self.schedule_update_ha_state()

    def update_callback(self):
        _LOGGER.debug(f"update_callback S30InverterPowerSensor [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def available(self) -> bool:
        if self._system.diagLevel not in (1, 2):
            return False
        return super().available

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_IE").replace("-", "")

    @property
    def name(self):
        return self._myname

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {}

    @property
    def native_value(self):
        if (
            self._system.diagInverterInputVoltage is None
            or self._system.diagInverterInputCurrent is None
        ):
            _LOGGER.debug(f"Values are None for diagnostic sensors  [{self._myname}]")
            return None
        if (
            self._system.diagInverterInputVoltage == "waiting..."
            or self._system.diagInverterInputCurrent == "waiting..."
        ):
            _LOGGER.debug(
                f"System is waiting for values for diagnostic sensors  [{self._myname}]"
            )
            return None
        try:
            return int(
                float(self._system.diagInverterInputVoltage)
                * float(self._system.diagInverterInputCurrent)
            )
        except ValueError as e:
            _LOGGER.warning(
                f"state myname [{self._myname}] diagInverterInputVoltage [{self._system.diagInverterInputVoltage}] diagInverterInputCurrent [{self._system.diagInverterInputCurrent}] failed: {e}"
            )
            pass
        return None

    @property
    def native_unit_of_measurement(self):
        return POWER_WATT

    @property
    def device_class(self):
        return SensorDeviceClass.POWER

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, self._system.unique_id() + "_ou")},
        }
