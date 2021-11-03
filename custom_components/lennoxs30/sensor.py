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

from lennoxs30api import lennox_system, lennox_zone


from homeassistant.components.sensor import (
    #    STATE_CLASS_MEASUREMENT,
    SensorEntity,
    PLATFORM_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lennoxs30"


async def async_setup_platform(
    hass, config, add_entities, discovery_info: Manager = None
) -> bool:
    _LOGGER.debug("sensor:async_setup_platform enter")
    # Discovery info is the API that we passed in.
    if discovery_info is None:
        _LOGGER.error(
            "sensor:async_setup_platform expecting API in discovery_info, found None"
        )
        return False
    theType = str(type(discovery_info))
    if "Manager" not in theType:
        _LOGGER.error(
            f"sensor:async_setup_platform expecting Manaager in discovery_info, found [{theType}]"
        )
        return False

    sensor_list = []
    manager: Manager = discovery_info
    for system in manager._api.getSystems():
        _LOGGER.info(f"Create S30OutdoorTempSensor sensor system [{system.sysId}]")
        sensor = S30OutdoorTempSensor(hass, manager, system)
        sensor_list.append(sensor)
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
        add_entities(sensor_list, True)
        _LOGGER.debug(
            f"climate:async_setup_platform exit - created [{len(sensor_list)}] entitites"
        )
        return True
    else:
        _LOGGER.info(
            f"climate:async_setup_platform exit - no system outdoor temperatures found"
        )
        return False


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
        _LOGGER.info(f"update_callback S30OutdoorTempSensor myname [{self._myname}]")
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

    # @property
    # def state_class(self):
    #    return STATE_CLASS_MEASUREMENT


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
        _LOGGER.info(f"update_callback S30TempSensor myname [{self._myname}]")
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


class S30HumiditySensor(SensorEntity):
    """Class for Lennox S30 thermostat temperature."""

    def __init__(self, hass: HomeAssistant, manager: Manager, zone: lennox_zone):
        self._hass = hass
        self._manager = manager
        self._zone = zone
        self._zone.registerOnUpdateCallback(self.update_callback, ["humidity"])
        self._myname = self._zone._system.name + "_" + self._zone.name + "_humidity"

    def update_callback(self):
        _LOGGER.info(f"update_callback S30HumiditySensor myname [{self._myname}]")
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
