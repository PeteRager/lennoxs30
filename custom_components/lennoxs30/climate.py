"""Support for Lennoxs30 Climate Entity"""
from __future__ import annotations

import logging
from typing import Any

from lennoxs30api import (
    LENNOX_HUMID_OPERATION_DEHUMID,
    LENNOX_HUMID_OPERATION_WAITING,
    LENNOX_HVAC_HEAT_COOL,
    S30Exception,
    lennox_system,
    lennox_zone,
)
from lennoxs30api.s30api_async import (
    LENNOX_HVAC_COOL,
    LENNOX_HVAC_EMERGENCY_HEAT,
    LENNOX_HVAC_HEAT,
    LENNOX_HVAC_OFF,
)
from .const import MANAGER

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    CURRENT_HVAC_DRY,
    CURRENT_HVAC_IDLE,
    FAN_AUTO,
    FAN_OFF,
    FAN_ON,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_NONE,
    SUPPORT_AUX_HEAT,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_HUMIDITY,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from . import Manager
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)

# HA doesn't have a 'circulate' state defined for fan.
FAN_CIRCULATE = "circulate"
# Additional Presets
PRESET_CANCEL_HOLD = "cancel hold"
PRESET_CANCEL_AWAY_MODE = "cancel away mode"
PRESET_SCHEDULE_OVERRIDE = "Schedule Hold"
# Basic set of support flags for every HVAC setup
SUPPORT_FLAGS = SUPPORT_PRESET_MODE | SUPPORT_FAN_MODE
# Standard set of fan modes
FAN_MODES = [FAN_AUTO, FAN_ON, FAN_CIRCULATE]

DOMAIN = "lennoxs30"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    _LOGGER.debug("climate:async_setup_platform enter")
    climate_list = []
    manager: Manager = hass.data[DOMAIN][entry.unique_id][MANAGER]
    for system in manager._api.getSystems():
        for zone in system.getZones():
            if zone.is_zone_active() == True:
                _LOGGER.debug(
                    f"Create S30 Climate system [{system.sysId}] zone [{zone.name}]  metric [{manager._is_metric}]"
                )
                climate = S30Climate(hass, manager, system, zone)
                climate_list.append(climate)
            else:
                _LOGGER.debug(
                    f"Skipping inactive zone - system [{system.sysId}] zone [{zone.name}]"
                )
    if len(climate_list) != 0:
        async_add_entities(climate_list, True)
        _LOGGER.debug(
            f"climate:async_setup_platform exit - created [{len(climate_list)}] entitites"
        )
        return True
    else:
        _LOGGER.error(f"climate:async_setup_platform exit - no climate entities found")
        return False


class S30Climate(ClimateEntity):
    """Class for Lennox S30 thermostat."""

    def __init__(
        self, hass, manager: Manager, system: lennox_system, zone: lennox_zone
    ):
        """Initialize the climate device."""
        self.hass: HomeAssistant = hass
        self._manager: Manager = manager
        self._system = system
        self._zone = zone
        self._zone.registerOnUpdateCallback(self.zone_update_callback)
        # We need notification of state of system.manualAwayMode in order to update the preset mode in HA.
        self._system.registerOnUpdateCallback(
            self.system_update_callback,
            [
                "manualAwayMode",
                "sa_enabled",
                "sa_state",
                "sa_reset",
                "sa_cancel",
                "sa_setpointState",
            ],
        )
        self._myname = self._system.name + "_" + self._zone.name

    @property
    def unique_id(self) -> str:
        return self._zone.unique_id

    def zone_update_callback(self):
        self.schedule_update_ha_state()

    def system_update_callback(self):
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs: dict[str, Any] = {}
        attrs["allergenDefender"] = self._zone.allergenDefender
        attrs["damper"] = self._zone.damper
        attrs["demand"] = self._zone.demand
        if self._zone.fan == True:
            attrs["fan"] = FAN_ON
        else:
            attrs["fan"] = FAN_OFF
        attrs["humOperation"] = self._zone.humOperation
        attrs["tempOperation"] = self._zone.tempOperation
        attrs["ventilation"] = self._zone.ventilation
        attrs["heatCoast"] = self._zone.heatCoast
        attrs["defrost"] = self._zone.defrost
        attrs["balancePoint"] = self._zone.balancePoint
        attrs["aux"] = self._zone.aux
        attrs["coolCoast"] = self._zone.coolCoast
        attrs["ssr"] = self._zone.ssr
        return attrs

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

    def is_single_setpoint_active(self) -> bool:
        # If the system is configured to use a single setpoint for both heat and cool
        if self._zone._system.single_setpoint_mode == True:
            return True
        # If it's in heat and cool then there are two setpoints
        if self._zone.systemMode == LENNOX_HVAC_HEAT_COOL:
            return False
        # All other modes just have one
        return True

    @property
    def supported_features(self):
        mask = SUPPORT_FLAGS

        # Target temperature.
        # If its a cooling or heating only system, then there is only one setpoint
        if self.is_single_setpoint_active() == True:
            mask |= SUPPORT_TARGET_TEMPERATURE
        else:
            mask |= SUPPORT_TARGET_TEMPERATURE_RANGE

        if (
            self._zone.humidificationOption == True
            or self._zone.dehumidificationOption == True
        ):
            mask |= SUPPORT_TARGET_HUMIDITY

        if (
            self._zone.heatingOption == True
            and self._system.has_emergency_heat() == True
        ):
            mask |= SUPPORT_AUX_HEAT

        _LOGGER.debug(
            "climate:supported_features name["
            + self._myname
            + "] support_flags ["
            + str(SUPPORT_FLAGS)
            + "]"
        )
        """Return the list of supported features."""
        return mask

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        if self._manager._is_metric is False:
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._zone.systemMode == LENNOX_HVAC_OFF:
            return None
        if self._zone.systemMode == LENNOX_HVAC_COOL:
            if self._manager._is_metric is False:
                return self._zone.minCsp
            return self._zone.minCspC
        if self._zone.systemMode == LENNOX_HVAC_HEAT:
            if self._manager._is_metric is False:
                return self._zone.minHsp
            return self._zone.minHspC
        if (
            self._zone.systemMode == LENNOX_HVAC_HEAT_COOL
            and self._system.single_setpoint_mode == True
        ):
            if self._manager._is_metric is False:
                return self._zone.minCsp
            return self._zone.minCspC
        # Single Setpoint Mode Not Enabled
        if self._zone.systemMode == LENNOX_HVAC_HEAT_COOL:
            if self._manager._is_metric is False:
                return self._zone.minHsp
            return self._zone.minHspC
        _LOGGER.warning(
            f"min_temp - unexpected system mode {self._zone.systemMode} returning default - please raise an issue"
        )
        return super().min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._zone.systemMode == LENNOX_HVAC_OFF or self._zone.systemMode == None:
            return None
        if self._zone.systemMode == LENNOX_HVAC_COOL:
            if self._manager._is_metric is False:
                return self._zone.maxCsp
            return self._zone.maxCspC
        if self._zone.systemMode == LENNOX_HVAC_HEAT:
            if self._manager._is_metric is False:
                return self._zone.maxHsp
            return self._zone.maxHspC
        if (
            self._zone.systemMode == LENNOX_HVAC_HEAT_COOL
            and self._system.single_setpoint_mode == True
        ):
            if self._manager._is_metric is False:
                return self._zone.maxHsp
            return self._zone.maxHspC
        # Single Setpoint Mode Not Enabled
        if self._zone.systemMode == LENNOX_HVAC_HEAT_COOL:
            if self._manager._is_metric is False:
                return self._zone.maxCsp
            return self._zone.maxCspC
        _LOGGER.warning(
            f"max_temp - unexpected system mode {self._zone.systemMode} returning default - please raise an issue"
        )
        return super().max_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._manager._is_metric is False:
            return self._zone.getTargetTemperatureF()
        else:
            return self._zone.getTargetTemperatureC()

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._manager._is_metric is False:
            t = self._zone.getTemperature()
            _LOGGER.debug(
                f"climate:current_temperature name [{self._myname}] temperature [{t}] F"
            )
        else:
            t = self._zone.getTemperatureC()
            _LOGGER.debug(
                f"climate:current_temperature name [{self._myname}] temperature [{t}] C"
            )
        return t

    @property
    def target_temperature_high(self):
        if self.is_single_setpoint_active() == True:
            return None
        """Return the highbound target temperature we try to reach."""
        if self._manager._is_metric is False:
            _LOGGER.debug(
                f"climate:target_temperature_high name [{self._myname}] temperature [{self._zone.csp}] F"
            )
            return self._zone.csp
        else:
            _LOGGER.debug(
                f"climate:target_temperature_high name [{self._myname}] temperature [{self._zone.cspC}] C"
            )
            return self._zone.cspC

    @property
    def target_temperature_low(self):
        if self.is_single_setpoint_active() == True:
            return None
        """Return the lowbound target temperature we try to reach."""
        if self._manager._is_metric is False:
            _LOGGER.debug(
                f"climate:target_temperature_low name [{self._myname}] temperature [{self._zone.hsp}] F"
            )
            return self._zone.hsp
        else:
            _LOGGER.debug(
                f"climate:target_temperature_low name [{self._myname}] temperature [{self._zone.hspC}] C"
            )
            return self._zone.hspC

    @property
    def current_humidity(self):
        """Return the current humidity."""
        h = self._zone.getHumidity()
        _LOGGER.debug(f"climate:current_humidity name [{self._myname}] humidity [{h}]")
        return h

    @property
    def hvac_mode(self):
        """Return the current hvac operation mode."""
        r = self._zone.getSystemMode()
        if r == LENNOX_HVAC_HEAT_COOL:
            r = HVAC_MODE_HEAT_COOL
        elif r == LENNOX_HVAC_EMERGENCY_HEAT:
            r = HVAC_MODE_HEAT
        _LOGGER.debug(f"climate:hvac_mode name [{self._myname}] mode [{r}]")
        return r

    @property
    def target_temperature_step(self) -> float:
        if self._manager._is_metric is False:
            return 1.0
        return 0.5

    @property
    def target_humidity(self) -> float:
        return self._zone.desp

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
        if self._zone.coolingOption == True and self._zone.heatingOption == True:
            modes.append(HVAC_MODE_HEAT_COOL)
        return modes

    async def async_trigger_fast_poll(self) -> None:
        self._manager._mp_wakeup_event.set()

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new hvac operation mode."""
        try:
            t_hvac_mode = hvac_mode
            # Only this mode needs to be mapped
            if t_hvac_mode == HVAC_MODE_HEAT_COOL:
                t_hvac_mode = LENNOX_HVAC_HEAT_COOL
            _LOGGER.debug(
                "climate:async_set_hvac_mode zone ["
                + self._myname
                + "] ha_mode ["
                + str(hvac_mode)
                + "] lennox_mode ["
                + t_hvac_mode
                + "]"
            )
            await self._zone.setHVACMode(t_hvac_mode)
            await self.async_trigger_fast_poll()
        except S30Exception as e:
            _LOGGER.error(e.message)
        except Exception as e:
            _LOGGER.error(str(e))

    @property
    def hvac_action(self):
        """Return the current hvac state/action."""
        # TODO may need to translate
        to = self._zone.tempOperation
        ho = self._zone.humOperation
        if to != "off":
            return to
        if ho != "off":
            if ho == LENNOX_HUMID_OPERATION_DEHUMID:
                return CURRENT_HVAC_DRY
            if ho == LENNOX_HUMID_OPERATION_WAITING:
                return CURRENT_HVAC_IDLE
            return ho
        if to == "off" and self._zone.systemMode != "off":
            return CURRENT_HVAC_IDLE
        return to

    @property
    def preset_mode(self):
        if self._system.get_away_mode() == True:
            return PRESET_AWAY
        if self._zone.overrideActive == True:
            return PRESET_SCHEDULE_OVERRIDE
        if self._zone.isZoneManualMode() == True:
            return PRESET_NONE
        scheduleId = self._zone.scheduleId
        if scheduleId is None:
            return PRESET_NONE
        schedule = self._system.getSchedule(scheduleId)
        if schedule is None:
            return PRESET_NONE
        return schedule.name

    @property
    def preset_modes(self):
        presets = []
        for schedule in self._system.getSchedules():
            # Everything above 16 seems to be internal schedules
            if schedule.id >= 16:
                continue
            presets.append(schedule.name)
        presets.append(PRESET_AWAY)
        presets.append(PRESET_CANCEL_HOLD)
        presets.append(PRESET_CANCEL_AWAY_MODE)
        presets.append(PRESET_NONE)
        _LOGGER.debug(
            "climate:preset_modes name["
            + self._myname
            + "] presets["
            + str(presets)
            + "]"
        )
        return presets

    async def async_set_preset_mode(self, preset_mode):
        try:
            _LOGGER.debug(
                "climate:async_set_preset_mode name["
                + self._myname
                + "] preset_mode ["
                + preset_mode
                + "]"
            )

            if preset_mode == PRESET_CANCEL_AWAY_MODE:
                processed = False
                if self._system.get_manual_away_mode() == True:
                    await self._system.set_manual_away_mode(False)
                    processed = True
                if self._system.get_smart_away_mode() == True:
                    await self._system.cancel_smart_away()
                    processed = True
                if processed == False:
                    _LOGGER.warning(
                        "Ignoring request to cancel away mode because system is not in away mode"
                    )
                    return
                await self.async_trigger_fast_poll()
                return
            if preset_mode == PRESET_AWAY:
                await self._system.set_manual_away_mode(True)
                await self.async_trigger_fast_poll()
                return
            # Need to cancel away modes before requesting a new preset
            if self._system.get_manual_away_mode() == True:
                await self._system.set_manual_away_mode(False)
            if self._system.get_smart_away_mode() == True:
                await self._system.cancel_smart_away()

            if preset_mode == PRESET_CANCEL_HOLD:
                await self._zone.setScheduleHold(False)
            elif preset_mode == PRESET_NONE:
                await self._zone.setManualMode()
            else:
                await self._zone.setSchedule(preset_mode)

            await self.async_trigger_fast_poll()

        except S30Exception as e:
            _LOGGER.error("async_set_preset_mode error:" + e.message)
        except Exception as e:
            _LOGGER.error("async_set_preset_mode error:" + str(e))

    @property
    def is_away_mode_on(self):
        """Return the current away mode status."""
        return self._system.get_away_mode()

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        return self._zone.getFanMode()

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return FAN_MODES

    @property
    def is_aux_heat(self) -> bool | None:
        res = self._zone.systemMode == LENNOX_HVAC_EMERGENCY_HEAT
        return res

    async def async_turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        try:
            _LOGGER.debug(f"climate:async_turn_aux_heat_on zone [{self._myname}]")
            await self._zone.setHVACMode(LENNOX_HVAC_EMERGENCY_HEAT)
            await self.async_trigger_fast_poll()
        except S30Exception as e:
            _LOGGER.error(e.message)
        except Exception as e:
            _LOGGER.error(str(e))

    async def async_turn_aux_heat_off(self):
        try:
            _LOGGER.debug(f"climate:async_turn_aux_heat_off zone [{self._myname}]")
            # When Aux is turned off, we will revert the zone to Heat Mode.
            await self._zone.setHVACMode(LENNOX_HVAC_HEAT)
            await self.async_trigger_fast_poll()
        except S30Exception as e:
            _LOGGER.error(e.message)
        except Exception as e:
            _LOGGER.error(str(e))

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature"""
        r_hvacMode = None
        if kwargs.get(ATTR_HVAC_MODE) is not None:
            r_hvacMode = kwargs.get(ATTR_HVAC_MODE)
        r_temperature = None
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            r_temperature = kwargs.get(ATTR_TEMPERATURE)
        r_csp = None
        if kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None:
            r_csp = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        r_hsp = None
        if kwargs.get(ATTR_TARGET_TEMP_LOW) is not None:
            r_hsp = kwargs.get(ATTR_TARGET_TEMP_LOW)

        _LOGGER.debug(
            f"climate:async_set_temperature zone [{self._myname}] hvacMode [{r_hvacMode}] temperature [{r_temperature}] temp_high [{r_csp}] temp_low [{r_hsp}]"
        )

        # A temperature must be specified
        if r_temperature is None and r_csp is None and r_hsp is None:
            msg = f"climate:async_set_temperature - no temperature given zone [{self._myname}]] hvacMode [{r_hvacMode}] temperature [{r_temperature}] temp_high [{r_csp}] temp_low [{r_hsp}]"
            _LOGGER.error(msg)
            return

        # Either provide temperature or high/low but not both
        if r_temperature != None and (r_csp != None or r_hsp != None):
            msg = f"climate:async_set_temperature - pass either temperature or temp_high / low - zone [{self._myname}] hvacMode [{r_hvacMode}] temperature [{r_temperature}] temp_high [{r_csp}] temp_low [{r_hsp}]"
            _LOGGER.error(msg)
            return

        # If no temperature, must specify both high and low
        if r_temperature == None and (r_csp == None or r_hsp == None):
            msg = f"climate:async_set_temperature - must provide both temp_high / low - zone [{self._myname}] hvacMode [{r_hvacMode}] temperature [{r_temperature}] temp_high [{r_csp}] temp_low [{r_hsp}]"
            _LOGGER.error(msg)
            return

        # If single setpoint mode, then must specify r_temperature and not high and low
        if self._zone._system.single_setpoint_mode == True:
            if r_temperature == None:
                msg = f"climate:async_set_temperature - zone in single setpoint mode must provide [{ATTR_TEMPERATURE}] - zone [{self._myname}]"
                _LOGGER.error(msg)
                return
            if r_hsp != None or r_csp != None:
                msg = f"climate:async_set_temperature - zone in single setpoint mode - do not set HIGH and LOW - zone [{self._myname}] hvacMode [{r_hvacMode}] temperature [{r_temperature}] temp_high [{r_csp}] temp_low [{r_hsp}]"
                _LOGGER.error(msg)
                return

        try:
            # If an HVAC mode is requested; and we are not in that mode, then the first step
            # is to switch the zone into that mode before setting the temperature
            if r_hvacMode != None and r_hvacMode != self.hvac_mode:
                _LOGGER.debug(
                    f"climate:async_set_temperature zone [{self._myname}] setting hvacMode [{r_hvacMode}]"
                )
                await self.async_set_hvac_mode(r_hvacMode)

            if r_hvacMode == None:
                r_hvacMode = self.hvac_mode

            if r_hvacMode == None:
                _LOGGER.error(
                    f"set_temperature System Mode is [{r_hvacMode}] unable to set temperature"
                )
                return

            if r_temperature is not None:
                if self._zone._system.single_setpoint_mode == True:
                    _LOGGER.debug(
                        f"climate:async_set_temperature set_temperature in single_setpoint_modesystem - zone [{self._myname}] temperature [{r_temperature}]"
                    )
                    if self._manager._is_metric is False:
                        await self._zone.perform_setpoint(r_sp=r_temperature)
                    else:
                        await self._zone.perform_setpoint(r_spC=r_temperature)
                elif self.hvac_mode == HVAC_MODE_COOL:
                    _LOGGER.debug(
                        f"climate:async_set_temperature set_temperature system in cool mode - zone [{self._myname}] temperature [{r_temperature}]"
                    )
                    if self._manager._is_metric is False:
                        await self._zone.perform_setpoint(r_csp=r_temperature)
                    else:
                        await self._zone.perform_setpoint(r_cspC=r_temperature)
                elif self.hvac_mode == HVAC_MODE_HEAT:
                    _LOGGER.debug(
                        f"climate:async_set_temperature set_temperature system in heat mode - zone [{self._myname}] sp [{r_temperature}]"
                    )
                    if self._manager._is_metric is False:
                        await self._zone.perform_setpoint(r_hsp=r_temperature)
                    else:
                        await self._zone.perform_setpoint(r_hspC=r_temperature)
                else:
                    _LOGGER.error(
                        f"set_temperature System Mode is [{r_hvacMode}] unable to set temperature"
                    )
                    return
            else:
                _LOGGER.debug(
                    "climate:async_set_temperature zone ["
                    + self._myname
                    + "] csp ["
                    + str(r_csp)
                    + "] hsp ["
                    + str(r_hsp)
                    + "]"
                )
                if self._manager._is_metric is False:
                    await self._zone.perform_setpoint(r_hsp=r_hsp, r_csp=r_csp)
                else:
                    await self._zone.perform_setpoint(r_hspC=r_hsp, r_cspC=r_csp)

            await self.async_trigger_fast_poll()

        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("climate:async_set_temperature - error:" + e.message)
            else:
                _LOGGER.error("climate:async_set_temperature - error:" + str(e))

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        _LOGGER.debug(
            f"climate:async_set_fan_mode name[{self._myname}] fanMode [{fan_mode}]"
        )
        try:
            await self._zone.setFanMode(fan_mode)
            await self.async_trigger_fast_poll()

        except Exception as e:
            if hasattr(e, "message"):
                _LOGGER.error("climate:async_set_fan_mode - error:" + e.message)
            else:
                _LOGGER.error("climate:async_set_fan_mode - error:" + str(e))

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        result = {
            "identifiers": {(DOMAIN, self.unique_id)},
        }
        return result
