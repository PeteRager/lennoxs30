"""Support for Lennoxs30 outdoor temperature sensor"""
from .const import MANAGER
from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_CURRENT,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    ELECTRIC_CURRENT_AMPERE,
    VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE,
    ELECTRIC_POTENTIAL_VOLT,
)
from . import Manager
from homeassistant.core import HomeAssistant
import logging
from lennoxs30api import lennox_system, lennox_zone
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:

    sensor_list = []

    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager._api.getSystems():
        _LOGGER.info(f"Create S30OutdoorTempSensor sensor system [{system.sysId}]")
        sensor = S30OutdoorTempSensor(hass, manager, system)
        sensor_list.append(sensor)
        if manager._create_inverter_power == True:
            _LOGGER.info(
                f"Create S30InverterPowerSensor sensor system [{system.sysId}]"
            )
            if system.diagLevel == None or system.diagLevel == 0:
                _LOGGER.warning(
                    f"Power Inverter Sensor requires S30 to be in diagLevel 1 or 2, currently in [{system.diagLevel}]"
                )
            power_sensor = S30InverterPowerSensor(hass, manager, system)
            sensor_list.append(power_sensor)
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
                    
            diagnostics = system.getDiagnostics()
            for e in diagnostics:
                for d in diagnostics[e]:
                    if(e>0): #equipment 0 has no diagnostic data
                        name = diagnostics[e][d]['name']
                        unit = diagnostics[e][d]['unit']
                        val = diagnostics[e][d]['value']
                        #_LOGGER.info(f"e {e} {d} {name} {unit}... {val}")
                        diagsensor = S30DiagSensor(hass, manager, system, e, d, name, unit)
                        sensor_list.append(diagsensor)

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

    def __init__(self, hass, manager, system, equipment, diagnostic, name, unit):
        self._hass = hass
        self._manager = manager
        self._system = system
        self.unit = unit
        self.rname = name
        self.equipment = equipment        
        self.diagnostic = diagnostic
        self.val = None
        self._system.registerOnUpdateCallbackDiag(
            self.update_callback, [ f"{equipment}_{diagnostic}"]
        )
        self._myname = self._system.name + f"_{equipment}_{diagnostic}_{name}".replace(" ","_")

    def update_callback(self, newval):
        #_LOGGER.info(f"update_callback S30DiagSSensor myname [{self._myname}] value {newval}")
        self.val = newval
        self.schedule_update_ha_state()


    @property
    def native_value(self):
        """Return native value of the sensor."""
        #_LOGGER.info(f"native_value S30DiagSSensor myname [{self._myname}] value {self.val}")
        return self.val

    @property
    def state(self):
       """Return native value of the sensor."""
       val = self._system.getDiagnostics()[self.equipment][self.diagnostic]['value']
       #_LOGGER.info(f"state S30DiagSSensor myname [{self._myname}] value {val}")
       return val

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
        return (self._myname).replace("-", "")


    @property
    def name(self):
        return f"{self.rname}"

    @property
    def unit_of_measurement(self):
        if "TemperatureC" in self.rname:
            return TEMP_CELSIUS
        elif "Temperature" in self.rname:
            return TEMP_FAHRENHEIT
        elif "Hz" in self.rname:
            return FREQUENCY_HERTZ
        elif "V" in self.unit:
            return ELECTRIC_POTENTIAL_VOLT
        elif "F" in self.unit:
            return TEMP_FAHRENHEIT          
        elif "A" in self.unit:
            return ELECTRIC_CURRENT_AMPERE
        elif "CFM" in self.unit:
            return VOLUME_FLOW_RATE_CUBIC_FEET_PER_MINUTE    
        return self.unit

    @property
    def device_class(self):
        if self.unit_of_measurement == TEMP_FAHRENHEIT:
            return DEVICE_CLASS_TEMPERATURE
        elif self.unit_of_measurement == TEMP_CELSIUS:
            return DEVICE_CLASS_TEMPERATURE
        elif self.unit_of_measurement == ELECTRIC_POTENTIAL_VOLT:
            return DEVICE_CLASS_VOLTAGE       
        elif self.unit_of_measurement == ELECTRIC_CURRENT_AMPERE:
            return DEVICE_CLASS_CURRENT
        elif self.unit_of_measurement == FREQUENCY_HERTZ:
            return DEVICE_CLASS_FREQUENCY
        return None

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        #TODO - use equipment type instad of hard coding
        if self.equipment == 1:
            return {
                "identifiers": {(DOMAIN, self._system.unique_id() + "_ou")},
            }
        else: 
            return {
                "identifiers": {(DOMAIN, self._system.unique_id() + "_iu")},
            }


class S30OutdoorTempSensor(SensorEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._system.registerOnUpdateCallback(
            self.update_callback, ["outdoorTemperature", "outdoorTemperatureC"]
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
