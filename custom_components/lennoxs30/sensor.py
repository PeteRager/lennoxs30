"""Support for Lennoxs30 outdoor temperature sensor"""
from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
)
from . import Manager
from homeassistant.core import HomeAssistant
import logging
from homeassistant.helpers.entity import DeviceInfo
from lennoxs30api import lennox_system, lennox_zone


from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
    PLATFORM_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"

async def async_setup_entry(hass, config, async_add_entities, discovery_info: Manager = None ) -> bool:
    
    _LOGGER.debug("sensor:async_setup_platform enter")
    
    hub_name = "lennoxs30"
    manager = hass.data[DOMAIN][hub_name]["hub"]
    sensor_list = []
    for system in manager._api.getSystems():
        _LOGGER.info(f"Create S30 S30OutdoorTempSensor sensor system [{system.sysId}]")
        if manager._is_metric:
            nativevalue = system.outdoorTemperatureC 
            nativeunit = TEMP_CELSIUS
        else:
            nativevalue = system.outdoorTemperature
            nativeunit = TEMP_FAHRENHEIT
        sensor_list.append( S30Sensor(hass, manager, system, "Outdoor_Temperature", nativevalue, nativeunit, DEVICE_CLASS_TEMPERATURE, STATE_CLASS_MEASUREMENT))
        if manager._createSensors == True:
            for zone in system.getZoneList():
                if zone.is_zone_active() == True:
                    if manager._is_metric:
                        nativevalue = zone.getTemperatureC()
                    else:
                        nativevalue = zone.getTemperature()
                    sensor_list.append( S30Sensor(hass, manager, system, zone.name + "_temperature", nativevalue, nativeunit, DEVICE_CLASS_TEMPERATURE, STATE_CLASS_MEASUREMENT))
                    sensor_list.append( S30Sensor(hass, manager, system, zone.name + "_humdity", zone.getHumidity(), PERCENTAGE, DEVICE_CLASS_HUMIDITY, STATE_CLASS_MEASUREMENT))
    if len(sensor_list) != 0:
        async_add_entities(sensor_list, True)
        _LOGGER.debug(
            f"climate:async_setup_platform exit - created [{len(sensor_list)}] entitites"
        )
        return True
    else:
        _LOGGER.info(
            f"climate:async_setup_platform exit - no system outdoor temperatures found"
        )
        return False


class S30Sensor(SensorEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(self, hass: HomeAssistant, manager: Manager, system: lennox_system, name, nativevalue,  nativeunit, deviceclass, stateclass):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._system.registerOnUpdateCallback(self.update_callback)
        self._myname = self._system.name + "_" + name
        self._nativevalue = nativevalue
        self._nativeunit = nativeunit
        self._deviceclass = deviceclass
        self._stateclass = stateclass
        manager.async_add_lennoxs30_sensor(self)

    def update_callback(self):
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return self._myname.replace("-", "").replace(" ", "_")

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
    def native_value(self):
        return self._nativevalue

    @property
    def native_unit_of_measurement(self):
        return self._nativeunit

    @property
    def device_class(self):
        return self._deviceclass
        
    @property
    def unique_id(self) -> str:
        """Return unique ID of entity."""
        return f"{self._myname}"

    @property
    def state_class(self):
        return self._stateclass
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return {
            "name": self._system.name,
            "identifiers": {(DOMAIN, self._system.unique_id())},
            "manufacturer": "Lennox",
            "model": "Lennox S30",
        }
        
        