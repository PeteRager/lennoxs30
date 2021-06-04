import logging
import asyncio
from . import s30api_async

from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL, CURRENT_HVAC_HEAT, CURRENT_HVAC_IDLE, HVAC_MODE_DRY,
    HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL, PRESET_AWAY, SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE, SUPPORT_PRESET_MODE, SUPPORT_FAN_MODE,
    FAN_ON, FAN_AUTO, ATTR_TARGET_TEMP_LOW, ATTR_TARGET_TEMP_HIGH,
    PRESET_NONE,
)

from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL, CURRENT_HVAC_HEAT, CURRENT_HVAC_IDLE,
    HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL,
    HVAC_MODE_HEAT_COOL, PRESET_AWAY, SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE, SUPPORT_PRESET_MODE, SUPPORT_FAN_MODE,
    FAN_ON, FAN_AUTO, ATTR_TARGET_TEMP_LOW, ATTR_TARGET_TEMP_HIGH,
    PRESET_NONE,
)
from homeassistant.const import (
    CONF_USERNAME, CONF_PASSWORD, TEMP_CELSIUS, TEMP_FAHRENHEIT,
    ATTR_TEMPERATURE)

_LOGGER = logging.getLogger(__name__)
#_LOGGER.setLevel(logging.DEBUG)

# HA doesn't have a 'circulate' state defined for fan.
FAN_CIRCULATE = 'circulate'

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE |
                 SUPPORT_TARGET_TEMPERATURE_RANGE |
                 SUPPORT_PRESET_MODE |
                 SUPPORT_FAN_MODE)

FAN_MODES = [
    FAN_AUTO, FAN_ON, FAN_CIRCULATE
]

HVAC_MODES = [
    HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL, HVAC_MODE_HEAT_COOL
]

HVAC_ACTIONS = [
    CURRENT_HVAC_IDLE, CURRENT_HVAC_HEAT, CURRENT_HVAC_COOL
]

TEMP_UNITS = [
    TEMP_FAHRENHEIT, TEMP_CELSIUS
]

DOMAIN = "lennoxs30"

_LOGGER = logging.getLogger(__name__)

#def setup(hass, config):
#    print("setup")
#    return True

from homeassistant.const import (CONF_EMAIL, CONF_PASSWORD)


async def async_setup_platform(hass, config, add_entities, discovery_info: s30api_async.s30api_async=None ):
    # Discovery info is the API that we passed in.
    _LOGGER.debug("climate:async_setup_platform enter")
    if discovery_info is None:
        _LOGGER.error("climate:async_setup_platform expecting API in discovery_info, found None")
        return False
    theType = str(type(discovery_info))
    if 's30api_async' not in theType:
        _LOGGER.error("climate:async_setup_platform expecting API in discovery_info, found [" + str(theType) + "]")
        return False

    climate_list = []

    s30api = discovery_info
    for system in s30api.getSystems():
        for zone in system.getZones():
            if zone.getTemperature() != None:
                _LOGGER.info("Create S30 Climate system [" + system.sysId + "] zone [" + zone.name + "]")
                climate = S30Climate(hass, s30api, system, zone)
                climate_list.append(climate)
            else:
                _LOGGER.info("Skipping S30 Climate system [" + system.sysId + "] zone [" + zone.name + "]")

    add_entities(climate_list, True)
    _LOGGER.debug("climate:async_setup_platform exit")
    return True

class S30Climate(ClimateEntity):
    """Class for Lennox iComfort WiFi thermostat."""

    def __init__(self, hass, s30api: s30api_async, system: s30api_async.lennox_system, zone: s30api_async.lennox_zone):
        """Initialize the climate device."""
        self.hass = hass
        self._s30api = s30api
        self._system = system
        self._system.registerOnUpdateCallback(self.update_callback)
        self._zone = zone
        self._min_temp = 60
        self._max_temp = 80
        self._myname = self._system.name + '_' + self._zone.name
        #self.unique_id = self._system.sysId + '_' + str(self._zone.id)
        s = 'climate' + "." +  self._system.sysId + '-' + str(self._zone.id)
        s = s.replace("-","")
        #self.entity_id = s

    @property
    def unique_id(self) -> str:
        return (self._system.sysId + '_' + str(self._zone.id)).replace("-","")

    def update_callback(self):
        _LOGGER.warning("update_callback myname [" + self._myname + "]")
        self.async_schedule_update_ha_state()

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
    def supported_features(self):
        _LOGGER.debug("climate:supported_features name[" + self._myname + "] support_flags [" + str(SUPPORT_FLAGS) + "]")
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_FAHRENHEIT

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        minTemp = None
        if self._zone.heatingOption == True:
            minTemp = self._zone.minHsp
        if self._zone.coolingOption == True:
            if minTemp == None:
                minTemp = self._zone.minCsp
            else:
                minTemp = min(minTemp, self._zone.minCsp)
        if minTemp != None:
            return minTemp
        return super().min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""

        maxTemp = None
        if self._zone.heatingOption == True:
            minTemp = self._zone.maxHsp
        if self._zone.coolingOption == True:
            if maxTemp == None:
                maxTemp = self._zone.maxCsp
            else:
                maxTemp = max(maxTemp, self._zone.maxCsp)
        if maxTemp != None:
            return maxTemp
        return super().max_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._zone.getTargetTemperatureF()

    @property
    def current_temperature(self):
        """Return the current temperature."""
        t = self._zone.getTemperature()
        _LOGGER.debug("climate:current_temperature name[" + self._myname + "] temperature [" + str(t) + "]")
        return t

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        # TODO Need to figure out heatcool mode and the string, for now we will return csp
        _LOGGER.debug("climate:target_temperature_high name[" + self._myname + "] temperature [" + str(self._zone.csp) + "]")
        return self._zone.csp

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        # TODO Need to figure out heatcool mode and the string, for now we will return csp
        _LOGGER.debug("climate:target_temperature_low name[" + self._myname + "] temperature [" + str(self._zone.hsp) + "]")
        return self._zone.hsp

    @property
    def current_humidity(self):
        """Return the current humidity."""
        h = self._zone.getHumidity() 
        _LOGGER.debug("climate:current_temperature name[" + self._myname + "] humidity [" + str(h) + "]")
        return h
 
    @property
    def hvac_mode(self):
        """Return the current hvac operation mode."""
        r = self._zone.getSystemMode()
        _LOGGER.debug("climate:hvac_mode name[" + self._myname + "] mode [" + r + "]")
        return r

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        modes = []
        modes.append(HVAC_MODE_OFF)
        if self._zone.coolingOption == True:
            modes.append(HVAC_MODE_COOL)
        if self._zone.heatingOption == True:
            modes.append(HVAC_MODE_HEAT)
        if self._zone.dehumidificationOption == True:
            modes.append(HVAC_MODE_DRY)
        return modes

    @property
    def hvac_action(self):
        """Return the current hvac state/action."""
        # TODO may need to translate
        return self._zone.tempOperation

    @property
    def preset_mode(self):
        """Return the current preset mode."""
#       if self._api.away_mode == 1:
#            return PRESET_AWAY
        return None

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        return [PRESET_NONE, PRESET_AWAY]

    @property
    def is_away_mode_on(self):
        """Return the current away mode status."""
        return False
#       return self._api.away_mode

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        return self._zone.getFanMode()

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return FAN_MODES

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature"""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            sp = kwargs.get(ATTR_TEMPERATURE)
            if self.hvac_mode == HVAC_MODE_COOL:
                _LOGGER.info("set_temperature system in cool mode, setting csp [" + str(sp) + "]")
                await self._system.setCoolSPF(sp)
            elif self.hvac_mode == HVAC_MODE_HEAT:
                _LOGGER.info("set_temperature system in heat mode, setting hsp [" + str(sp) + "]")
                await self._system.setCoolSPF(sp)
            else:
                _LOGGER.error("set_temperature System Mode is [" + self.hvac_mode + "] unable to set temperature" )
        else:
            csp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            hsp = kwargs.get(ATTR_TARGET_TEMP_LOW)
            await self._system.setHeatCoolSPF(hsp, csp)
#            if self.hvac_mode == HVAC_MODE_COOL:
#                _LOGGER.info("set_temperature system in cool mode, setting csp [" + str(csp) + "]")
#                await self._system.setCoolSPF(csp)
#            elif self.hvac_mode == HVAC_MODE_HEAT:
#                _LOGGER.info("set_temperature system in heat mode, setting hsp [" + str(hsp) + "]")
#                await self._system.setHeatSPF(hsp)
#            else:
#                _LOGGER.error("set_temperature System Mode is [" + self.hvac_mode + "] unable to set temperature" )

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        await self._system.setFanMode(fan_mode)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new hvac operation mode."""
        await self._system.setHVACMode(hvac_mode)
        # We'll do a couple polls until we get the state
        for x in range(1, 10):
            await asyncio.sleep(0.5)
            await self._s30api.retrieve()
            if self._zone.getSystemMode() == hvac_mode:
                _LOGGER.info("async_set_hvac_mode - got change with fast poll iteration [" + str(x) + "]")
                return
        _LOGGER.info("async_set_hvac_mode - unabled to retrieve change with fast poll")

    def set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        print("TODO")
        
#        if preset_mode == PRESET_AWAY:
#            self._turn_away_mode_on()
#        else:
#            self._turn_away_mode_off()

    def _turn_away_mode_on(self):
        print("TODO")
#        """Turn away mode on."""
#        self._api.away_mode = 1

    def _turn_away_mode_off(self):
        print("TODO")
#        """Turn away mode off."""
#        self._api.away_mode = 0
