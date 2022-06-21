"""Support for Lennoxs30 outdoor temperature sensor"""
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
    LENNOX_STATUS_NOT_AVAILABLE,
    LENNOX_STATUS_NOT_EXIST,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory

from homeassistant.components.sensor import (
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
            if system.diagLevel == None or system.diagLevel == 0:
                _LOGGER.warning(
                    f"Power Inverter Sensor requires S30 to be in diagLevel 2 and isolated from the internet, currently in [{system.diagLevel}]"
                )
            power_sensor = S30InverterPowerSensor(hass, manager, system)
            sensor_list.append(power_sensor)

        if manager._create_diagnostic_sensors == True:
            _LOGGER.info(f"Create Diagnostic Sensors system [{system.sysId}]")
            if system.diagLevel == None or system.diagLevel == 0:
                _LOGGER.warning(
                    f"Diagnostics requires S30 to be in diagLevel 2 and isolated from the internet, currently in [{system.diagLevel}]"
                )
            diagnostics = system.getDiagnostics()
            for e in diagnostics:
                for d in diagnostics[e]:
                    if e > 0:  # equipment 0 has no diagnostic data
                        _LOGGER.info(
                            f"Create Diagsensor system [{system.sysId}] eid [{e}] did [{d}] name [{diagnostics[e][d]['name']}]"
                        )
                        diagsensor = S30DiagSensor(hass, manager, system, e, d)
                        sensor_list.append(diagsensor)

        if manager._createSensors == True:
            for zone in system.getZoneList():
                if zone.is_zone_active() == True:
                    _LOGGER.info(
                        f"Create S30TempSensor sensor system [{system.sysId}] zone [{zone.id}]"
                    )
                    tempSensor = S30TempSensor(hass, manager, zone)
                    sensor_list.append(tempSensor)
                    _LOGGER.info(
                        f"Create S30HumSensor sensor system [{system.sysId}] zone [{zone.id}]"
                    )
                    humSensor = S30HumiditySensor(hass, manager, zone)
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


class S30DiagSensor(SensorEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass, manager, system, eid, did):
        self._hass = hass
        self._manager = manager
        self._system: lennox_system = system
        self.rname = system.getDiagnostics()[eid][did]["name"]
        self.eid = eid
        self.did = did
        self._myname = self._system.name + f"_{eid}_{self.rname}".replace(" ", "_")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._system.registerOnUpdateCallbackDiag(
            self.update_callback, [f"{self.eid}_{self.did}"]
        )

    def update_callback(self, eid_did, newval):
        _LOGGER.debug(
            f"update_callback S30DiagSSensor myname [{self._myname}] value {newval}"
        )
        self.schedule_update_ha_state()

    @property
    def state(self):
        """Return native value of the sensor."""
        try:
            return self._system.getDiagnostics()[self.eid][self.did]["value"]
        except Exception as e:
            _LOGGER.error(f"Error getting state [{self._myname}] [{e}]")
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {}

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (
            f"{self._system.unique_id()}_{UNIQUE_ID_SUFFIX_DIAG_SENSOR}_{self.eid}_{self.rname}"
        ).replace("-", "")

    @property
    def name(self):
        return f"{self.rname}"

    @property
    def unit_of_measurement(self):
        unit = None
        try:
            unit = self._system.getDiagnostics()[self.eid][self.did]["unit"]
        except Exception as e:
            _LOGGER.error(f"Error getting unit [{self._myname}] [{e}]")
            return None

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
        return self.unit

    @property
    def device_class(self):
        if self.unit_of_measurement == TEMP_FAHRENHEIT:
            return SensorDeviceClass.TEMPERATURE
        elif self.unit_of_measurement == TEMP_CELSIUS:
            return SensorDeviceClass.TEMPERATURE
        elif self.unit_of_measurement == ELECTRIC_POTENTIAL_VOLT:
            return SensorDeviceClass.VOLTAGE
        elif self.unit_of_measurement == ELECTRIC_CURRENT_AMPERE:
            return SensorDeviceClass.CURRENT
        elif self.unit_of_measurement == FREQUENCY_HERTZ:
            return SensorDeviceClass.FREQUENCY
        return None

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        if self.eid == 1:
            return {
                "identifiers": {(DOMAIN, self._system.unique_id() + "_ou")},
            }
        if self.eid == 2:
            return {
                "identifiers": {(DOMAIN, self._system.unique_id() + "_iu")},
            }
        _LOGGER.warning(
            f"Unexpected equipment id [{self.eid}], please raise an issue and post a mesage log"
        )
        return {
            "identifiers": {(DOMAIN, self._system.unique_id())},
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class S30OutdoorTempSensor(SensorEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._system.registerOnUpdateCallback(
            self.update_callback,
            ["outdoorTemperature", "outdoorTemperatureC", "outdoorTemperatureStatus"],
        )
        self._myname = self._system.name + "_outdoor_temperature"

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

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        return self._myname

    @property
    def state(self):
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
    def unit_of_measurement(self):
        if self._manager._is_metric is False:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._system.unique_id() + "_ou")},
        }


class S30TempSensor(SensorEntity):
    """Class for Lennox S30 thermostat temperature."""

    def __init__(self, hass: HomeAssistant, manager: Manager, zone: lennox_zone):
        self._hass = hass
        self._manager = manager
        self._zone = zone
        self._zone.registerOnUpdateCallback(
            self.update_callback, ["temperature", "temperatureC"]
        )
        self._myname = self._zone._system.name + "_" + self._zone.name + "_temperature"

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

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        return self._myname

    @property
    def state(self):
        if self._manager._is_metric is False:
            return self._zone.getTemperature()
        return self._zone.getTemperatureC()

    @property
    def unit_of_measurement(self):
        if self._manager._is_metric is False:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
        }


class S30HumiditySensor(SensorEntity):
    """Class for Lennox S30 thermostat temperature."""

    def __init__(self, hass: HomeAssistant, manager: Manager, zone: lennox_zone):
        self._hass = hass
        self._manager = manager
        self._zone = zone
        self._zone.registerOnUpdateCallback(self.update_callback, ["humidity"])
        self._myname = self._zone._system.name + "_" + self._zone.name + "_humidity"

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

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        return self._myname

    @property
    def state(self):
        return self._zone.getHumidity()

    @property
    def unit_of_measurement(self):
        return PERCENTAGE

    @property
    def device_class(self):
        return DEVICE_CLASS_HUMIDITY

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._zone.unique_id)},
        }


class S30InverterPowerSensor(SensorEntity):
    """Class for Lennox S30 inverter power."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._system.registerOnUpdateCallback(
            self.update_callback,
            ["diagInverterInputVoltage", "diagInverterInputCurrent"],
        )
        self._myname = self._system.name + "_inverter_energy"

    def update_callback(self):
        _LOGGER.debug(f"update_callback S30InverterPowerSensor [{self._myname}]")
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.unique_id() + "_IE").replace("-", "")

    def update(self):
        """Update data from the thermostat API."""
        return True

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        return self._myname

    @property
    def state(self):
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
            _LOGGER.warning(f"state myname [{self._myname}] failed: {e}")
            pass
        return None

    @property
    def unit_of_measurement(self):
        return POWER_WATT

    @property
    def device_class(self):
        return DEVICE_CLASS_POWER

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, self._system.unique_id() + "_ou")},
        }
