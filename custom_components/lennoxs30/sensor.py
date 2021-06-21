from homeassistant.const import DEVICE_CLASS_TEMPERATURE, TEMP_FAHRENHEIT
from . import Manager
from homeassistant.core import HomeAssistant
import logging

from lennoxs30api import lennox_system


from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorEntity, PLATFORM_SCHEMA

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"

async def async_setup_platform(hass, config, add_entities, discovery_info: Manager=None ) -> bool:
    # Discovery info is the API that we passed in. 
    _LOGGER.debug("sensor:async_setup_platform enter")
    if discovery_info is None:
        _LOGGER.error("sensor:async_setup_platform expecting API in discovery_info, found None")
        return False
    theType = str(type(discovery_info))
    if 'Manager' not in theType:
        _LOGGER.error(f"sensor:async_setup_platform expecting Manaager in discovery_info, found [{theType}]")
        return False

    sensor_list = []
    manager: Manager = discovery_info
    for system in manager._api.getSystems():
        _LOGGER.info(f"Create S30 sensor system [{system.sysId}]")
        sensor = S30OutdoorTempSensor(hass, manager, system)
        sensor_list.append(sensor)
    if len(sensor_list) != 0:         
        add_entities(sensor_list, True)
        _LOGGER.debug(f"climate:async_setup_platform exit - created [{len(sensor_list)}] entitites")
        return True
    else:
        _LOGGER.info(f"climate:async_setup_platform exit - no system outdoor temperatures found")
        return False

class S30OutdoorTempSensor(SensorEntity):
    """Class for Lennox S30 thermostat."""
    def __init__(self, hass: HomeAssistant, manager: Manager, system:lennox_system):
        self._hass = hass
        self._manager = manager
        self._system = system
        self._system.registerOnUpdateCallback(self.update_callback)
        self._myname = self._system.name + '_outdoor_temperature'
         

    def update_callback(self):
        _LOGGER.info(f"update_callback myname [{self._myname}]")
#       self.async_schedule_update_ha_state()
        self.schedule_update_ha_state()        

    @property
    def unique_id(self) -> str:
        # HA fails with dashes in IDs
        return (self._system.sysId + '_OT').replace("-","")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {         
        }        

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
        return self._system.outdoorTemperature

    @property
    def unit_of_measurement(self):
        return TEMP_FAHRENHEIT

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    @property
    def state_class(self):
        return STATE_CLASS_MEASUREMENT