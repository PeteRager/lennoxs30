# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access

import logging
from unittest.mock import patch
import pytest

from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_NONE,
)

from homeassistant.components.climate.const import (
    CURRENT_HVAC_DRY,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    SUPPORT_AUX_HEAT,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_HUMIDITY,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)


from lennoxs30api.s30api_async import (
    LENNOX_HVAC_COOL,
    LENNOX_HVAC_HEAT,
    LENNOX_HVAC_HEAT_COOL,
    LENNOX_HVAC_OFF,
    LENNOX_SA_STATE_DISABLED,
    LENNOX_SA_SETPOINT_STATE_AWAY,
    LENNOX_TEMP_OPERATION_OFF,
    LENNOX_HUMID_OPERATION_OFF,
    LENNOX_HUMID_OPERATION_DEHUMID,
    LENNOX_TEMP_OPERATION_COOLING,
    LENNOX_HUMID_OPERATION_WAITING,
    LENNOX_HVAC_EMERGENCY_HEAT,
    LENNOX_SA_SETPOINT_STATE_HOME,
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    LENNOX_STATUS_GOOD,
    LENNOX_STATUS_NOT_AVAILABLE,
    LENNOX_STATUS_NOT_EXIST,
    LENNOX_ZONING_MODE_CENTRAL,
    LENNOX_ZONING_MODE_ZONED,
    lennox_system,
    lennox_zone,
    S30Exception,
)

from custom_components.lennoxs30 import (
    Manager,
)

from custom_components.lennoxs30.climate import (
    PRESET_CANCEL_AWAY_MODE,
    PRESET_CANCEL_HOLD,
    PRESET_SCHEDULE_OVERRIDE,
    S30Climate,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from tests.conftest import conftest_base_entity_availability


@pytest.mark.asyncio
async def test_climate_unique_id(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    assert c.unique_id == zone.unique_id
    assert c.name == system.name + "_" + zone.name


@pytest.mark.asyncio
async def test_climate_min_max_c(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    # Metric Tests
    assert manager.is_metric is True
    assert c.temperature_unit == TEMP_CELSIUS
    zone.systemMode = LENNOX_HVAC_OFF
    assert c.min_temp is None
    assert c.max_temp is None

    zone.systemMode = LENNOX_HVAC_COOL
    assert c.min_temp == zone.minCspC
    assert c.max_temp == zone.maxCspC

    zone.systemMode = LENNOX_HVAC_HEAT
    assert c.min_temp == zone.minHspC
    assert c.max_temp == zone.maxHspC

    assert system.single_setpoint_mode is True
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minCspC
    assert c.max_temp == zone.maxHspC

    system.single_setpoint_mode = False
    assert system.single_setpoint_mode is False
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minHspC
    assert c.max_temp == zone.maxCspC

    # Zoning tests, switching the central mode disabled all zone except zone 0
    zone1.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c1.min_temp == zone1.minHspC
    assert c1.max_temp == zone1.maxCspC
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.min_temp == zone.minHspC
    assert c.max_temp == zone.maxCspC
    assert c1.min_temp is None
    assert c1.max_temp is None


@pytest.mark.asyncio
async def test_climate_min_max_f(hass, manager_mz: Manager, caplog):
    manager: Manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    manager.is_metric = False

    assert manager.is_metric is False
    assert c.temperature_unit == TEMP_FAHRENHEIT
    zone.systemMode = LENNOX_HVAC_OFF
    assert c.min_temp is None
    assert c.max_temp is None

    zone.systemMode = LENNOX_HVAC_COOL
    assert c.min_temp == zone.minCsp
    assert c.max_temp == zone.maxCsp

    zone.systemMode = LENNOX_HVAC_HEAT
    assert c.min_temp == zone.minHsp
    assert c.max_temp == zone.maxHsp

    assert system.single_setpoint_mode is True
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minCsp
    assert c.max_temp == zone.maxHsp

    system.single_setpoint_mode = False
    assert system.single_setpoint_mode is False
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minHsp
    assert c.max_temp == zone.maxCsp

    # Zoning tests, switching the central mode disabled all zone except zone 0
    zone1.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c1.min_temp == zone1.minHsp
    assert c1.max_temp == zone1.maxCsp
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.min_temp == zone.minHsp
    assert c.max_temp == zone.maxCsp
    assert c1.min_temp is None
    assert c1.max_temp is None
    system.zoningMode = LENNOX_ZONING_MODE_ZONED

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        zone.systemMode = "INVALID_MODE"
        assert c.min_temp == 44.6
        assert c.max_temp == 95
        assert len(caplog.records) == 2


@pytest.mark.asyncio
async def test_climate_target_temperature_f(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert c.target_temperature == zone.getTargetTemperatureF()
    assert c1.target_temperature == zone1.getTargetTemperatureF()

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL

    assert c.target_temperature == zone.getTargetTemperatureF()
    assert c1.target_temperature is None


@pytest.mark.asyncio
async def test_climate_target_temperature_c(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    manager.is_metric = True
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert c.target_temperature == zone.getTargetTemperatureC()
    assert c1.target_temperature == zone1.getTargetTemperatureC()

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL

    assert c.target_temperature == zone.getTargetTemperatureC()
    assert c1.target_temperature is None


@pytest.mark.asyncio
async def test_climate_target_temperature_high_f(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_high is None
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_high is None

    system.single_setpoint_mode = False
    assert zone.systemMode == LENNOX_HVAC_HEAT
    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_high is None
    assert zone1.systemMode == LENNOX_HVAC_COOL
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_high is None

    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    zone1.systemMode = LENNOX_HVAC_HEAT_COOL

    assert c.is_single_setpoint_active() is False
    assert c.target_temperature_high == zone.csp
    assert c1.target_temperature_high == zone1.csp

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.target_temperature_high == zone.csp
    assert c1.target_temperature_high is None


@pytest.mark.asyncio
async def test_climate_target_temperature_high_c(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    manager.is_metric = True
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_high is None
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_high is None

    system.single_setpoint_mode = False
    assert zone.systemMode == LENNOX_HVAC_HEAT
    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_high is None
    assert zone1.systemMode == LENNOX_HVAC_COOL
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_high is None

    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    zone1.systemMode = LENNOX_HVAC_HEAT_COOL

    assert c.is_single_setpoint_active() is False
    assert c.target_temperature_high == zone.cspC
    assert c1.target_temperature_high == zone1.cspC

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.target_temperature_high == zone.cspC
    assert c1.target_temperature_high is None


@pytest.mark.asyncio
async def test_climate_target_temperature_low_f(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    manager.is_metric = False
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_low is None
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_low is None

    system.single_setpoint_mode = False
    assert zone.systemMode == LENNOX_HVAC_HEAT
    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_low is None
    assert zone1.systemMode == LENNOX_HVAC_COOL
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_low is None

    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    zone1.systemMode = LENNOX_HVAC_HEAT_COOL

    assert c.is_single_setpoint_active() is False
    assert c.target_temperature_low == zone.hsp
    assert c1.target_temperature_low == zone1.hsp

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.target_temperature_low == zone.hsp
    assert c1.target_temperature_low is None


@pytest.mark.asyncio
async def test_climate_target_temperature_low_c(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    manager.is_metric = True
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_low is None
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_low is None

    system.single_setpoint_mode = False
    assert zone.systemMode == LENNOX_HVAC_HEAT
    assert c.is_single_setpoint_active() is True
    assert c.target_temperature_low is None
    assert zone1.systemMode == LENNOX_HVAC_COOL
    assert c1.is_single_setpoint_active() is True
    assert c1.target_temperature_low is None

    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    zone1.systemMode = LENNOX_HVAC_HEAT_COOL

    assert c.is_single_setpoint_active() is False
    assert c.target_temperature_low == zone.hspC
    assert c1.target_temperature_low == zone1.hspC

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.target_temperature_low == zone.hspC
    assert c1.target_temperature_low is None


@pytest.mark.asyncio
async def test_climate_system_subscription(hass, manager_mz: Manager):
    manager: Manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {
            "enabled": not system.sa_enabled,
            "reset": not system.sa_reset,
            "cancel": not system.sa_cancel,
            "state": "Cancelled",
            "setpointState": "a setpoint state",
            "zoningMode": LENNOX_ZONING_MODE_CENTRAL,
        }
        system.attr_updater(update_set, "enabled", "sa_enabled")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        system.attr_updater(update_set, "reset", "sa_reset")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        system.attr_updater(update_set, "cancel", "sa_cancel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        system.attr_updater(update_set, "state", "sa_state")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 4
        system.attr_updater(update_set, "setpointState", "sa_setpointState")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 5
        system.attr_updater(update_set, "zoningMode", "zoningMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 6

    conftest_base_entity_availability(manager, system, c)

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        zone._dirty = True
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1


@pytest.mark.asyncio
async def test_climate_preset_mode(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert system.get_manual_away_mode() is True
    assert c.preset_mode == PRESET_AWAY
    system.manualAwayMode = False
    assert zone.scheduleId == zone.getManualModeScheduleId()
    assert c.preset_mode == PRESET_NONE
    system.sa_enabled = True
    assert zone.scheduleId == zone.getManualModeScheduleId()
    assert c.preset_mode == PRESET_NONE
    system.sa_setpointState = LENNOX_SA_SETPOINT_STATE_AWAY
    assert c.preset_mode == PRESET_AWAY
    system.sa_setpointState = LENNOX_SA_SETPOINT_STATE_HOME
    assert c.preset_mode == PRESET_NONE
    zone.scheduleId = 2
    assert c.preset_mode == "winter"
    zone.overrideActive = True
    assert c.preset_mode == PRESET_SCHEDULE_OVERRIDE

    # Zoning tests, switching the central mode disabled all zone except zone 0
    zone1.scheduleId = 2
    assert c1.preset_mode == "winter"
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.preset_mode == PRESET_SCHEDULE_OVERRIDE
    assert c1.preset_mode is None


@pytest.mark.asyncio
async def test_climate_set_preset_mode(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert system.get_manual_away_mode() is True
    assert system.get_smart_away_mode() is False
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_CANCEL_AWAY_MODE)
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 is False
            assert cancel_smart_away.call_count == 0

    system.sa_enabled = True
    system.sa_setpointState = LENNOX_SA_SETPOINT_STATE_AWAY
    assert system.get_manual_away_mode() is True
    assert system.get_smart_away_mode() is True
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_CANCEL_AWAY_MODE)
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 is False
            assert cancel_smart_away.call_count == 1

    system.manualAwayMode = False
    system.sa_enabled = True
    system.sa_setpoint_state = LENNOX_SA_SETPOINT_STATE_AWAY
    assert system.get_manual_away_mode() is False
    assert system.get_smart_away_mode() is True
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_CANCEL_AWAY_MODE)
            assert set_manual_away.call_count == 0
            assert cancel_smart_away.call_count == 1

    system.manualAwayMode = False
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() is False
    assert system.get_smart_away_mode() is False
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_AWAY)
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 is True
            assert cancel_smart_away.call_count == 0

    system.manualAwayMode = True
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() is True
    assert system.get_smart_away_mode() is False
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(zone, "setSchedule") as zone_set_schedule:
            await c.async_set_preset_mode("winter")
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 is False
            assert zone_set_schedule.call_count == 1
            arg0 = zone_set_schedule.await_args[0][0]
            assert arg0 == "winter"

    system.manualAwayMode = False
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() is False
    assert system.get_smart_away_mode() is False
    with patch.object(zone, "setScheduleHold") as zone_set_schedule_hold:
        await c.async_set_preset_mode(PRESET_CANCEL_HOLD)
        assert zone_set_schedule_hold.call_count == 1
        arg0 = zone_set_schedule_hold.await_args[0][0]
        assert arg0 is False

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL

    system.manualAwayMode = False
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() is False
    assert system.get_smart_away_mode() is False
    with patch.object(zone, "setManualMode") as zone_set_manual_mode:
        await c.async_set_preset_mode(PRESET_NONE)
        assert zone_set_manual_mode.call_count == 1

    # Should not be able to set preset when zone is disabled.
    with caplog.at_level(logging.ERROR):
        with patch.object(zone1, "setSchedule") as zone_set_scheduele:
            caplog.clear()
            await c1.async_set_preset_mode("winter")
            assert zone_set_scheduele.call_count == 0
            assert len(caplog.records) == 1

    with caplog.at_level(logging.ERROR):
        with patch.object(zone1, "setSchedule") as zone_set_scheduele:
            caplog.clear()
            await c.async_set_preset_mode("invaiid_preset")
            assert zone_set_scheduele.call_count == 0
            assert len(caplog.records) == 1
            assert "invaiid_preset" in caplog.messages[0]


@pytest.mark.asyncio
async def test_climate_extra_state_attributes(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    attrs = c.extra_state_attributes
    assert attrs["allergenDefender"] == zone.allergenDefender
    assert attrs["damper"] == zone.damper
    assert attrs["demand"] == zone.demand
    assert attrs["fan"] == "off"
    assert attrs["humidityMode"] == zone.humidityMode
    assert attrs["humOperation"] == zone.humOperation
    assert attrs["tempOperation"] == zone.tempOperation
    assert attrs["ventilation"] == zone.ventilation
    assert attrs["heatCoast"] == zone.heatCoast
    assert attrs["defrost"] == zone.defrost
    assert attrs["balancePoint"] == zone.balancePoint
    assert attrs["aux"] == zone.aux
    assert attrs["coolCoast"] == zone.coolCoast
    assert attrs["ssr"] == zone.ssr
    assert attrs["zoneEnabled"] is True
    assert attrs["zoningMode"] == system.zoningMode

    zone.fan = True
    attrs = c.extra_state_attributes
    assert attrs["allergenDefender"] == zone.allergenDefender
    assert attrs["damper"] == zone.damper
    assert attrs["demand"] == zone.demand
    assert attrs["fan"] == "on"
    assert attrs["humidityMode"] == zone.humidityMode
    assert attrs["humOperation"] == zone.humOperation
    assert attrs["tempOperation"] == zone.tempOperation
    assert attrs["ventilation"] == zone.ventilation
    assert attrs["heatCoast"] == zone.heatCoast
    assert attrs["defrost"] == zone.defrost
    assert attrs["balancePoint"] == zone.balancePoint
    assert attrs["aux"] == zone.aux
    assert attrs["coolCoast"] == zone.coolCoast
    assert attrs["ssr"] == zone.ssr
    assert attrs["zoneEnabled"] is True
    assert attrs["zoningMode"] == system.zoningMode

    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)
    attrs = c1.extra_state_attributes
    assert attrs["allergenDefender"] == zone1.allergenDefender
    assert attrs["damper"] == zone1.damper
    assert attrs["demand"] == zone1.demand
    assert attrs["fan"] == "on" if zone1.fan else "off"
    assert attrs["humidityMode"] == zone1.humidityMode
    assert attrs["humOperation"] == zone1.humOperation
    assert attrs["tempOperation"] == zone1.tempOperation
    assert attrs["ventilation"] == zone1.ventilation
    assert attrs["heatCoast"] == zone1.heatCoast
    assert attrs["defrost"] == zone1.defrost
    assert attrs["balancePoint"] == zone1.balancePoint
    assert attrs["aux"] == zone1.aux
    assert attrs["coolCoast"] == zone1.coolCoast
    assert attrs["ssr"] == zone1.ssr
    assert attrs["zoneEnabled"] is True
    assert attrs["zoningMode"] == system.zoningMode

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    attrs = c.extra_state_attributes
    assert attrs["allergenDefender"] == zone.allergenDefender
    assert attrs["damper"] == zone.damper
    assert attrs["demand"] == zone.demand
    assert attrs["fan"] == "on" if zone.fan else "off"
    assert attrs["humidityMode"] == zone.humidityMode
    assert attrs["humOperation"] == zone.humOperation
    assert attrs["tempOperation"] == zone.tempOperation
    assert attrs["ventilation"] == zone.ventilation
    assert attrs["heatCoast"] == zone.heatCoast
    assert attrs["defrost"] == zone.defrost
    assert attrs["balancePoint"] == zone.balancePoint
    assert attrs["aux"] == zone.aux
    assert attrs["coolCoast"] == zone.coolCoast
    assert attrs["ssr"] == zone.ssr
    assert attrs["zoneEnabled"] is True
    assert attrs["zoningMode"] == system.zoningMode

    attrs = c1.extra_state_attributes
    assert attrs["allergenDefender"] is None
    assert attrs["damper"] is None
    assert attrs["demand"] is None
    assert attrs["fan"] is None
    assert attrs["humidityMode"] is None
    assert attrs["humOperation"] is None
    assert attrs["tempOperation"] is None
    assert attrs["ventilation"] is None
    assert attrs["heatCoast"] is None
    assert attrs["defrost"] is None
    assert attrs["balancePoint"] is None
    assert attrs["aux"] is None
    assert attrs["coolCoast"] is None
    assert attrs["ssr"] is None
    assert attrs["zoneEnabled"] is False
    assert attrs["zoningMode"] == system.zoningMode


@pytest.mark.asyncio
async def test_climate_supported_features(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    feat = c.supported_features
    assert c.is_single_setpoint_active() is True
    assert feat & SUPPORT_TARGET_TEMPERATURE != 0
    assert feat & SUPPORT_TARGET_TEMPERATURE_RANGE == 0

    c._zone.system.single_setpoint_mode = False
    c._zone.systemMode = LENNOX_HVAC_HEAT_COOL
    feat = c.supported_features
    assert c.is_single_setpoint_active() is False
    assert feat & SUPPORT_TARGET_TEMPERATURE == 0
    assert feat & SUPPORT_TARGET_TEMPERATURE_RANGE != 0

    feat = c.supported_features
    assert c._zone.dehumidificationOption is True
    assert c._zone.humidificationOption is False
    assert c._zone.humidityMode == LENNOX_HUMIDITY_MODE_OFF
    assert feat & SUPPORT_TARGET_HUMIDITY == 0

    c._zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
    feat = c.supported_features
    assert feat & SUPPORT_TARGET_HUMIDITY != 0

    c._zone.dehumidificationOption = False
    c._zone.humidificationOption = True
    c._zone.humidityMode = LENNOX_HUMIDITY_MODE_OFF
    feat = c.supported_features
    assert feat & SUPPORT_TARGET_HUMIDITY == 0

    c._zone.humidityMode = LENNOX_HUMIDITY_MODE_HUMIDIFY
    feat = c.supported_features
    assert feat & SUPPORT_TARGET_HUMIDITY != 0

    c._zone.humidificationOption = False
    feat = c.supported_features
    assert feat & SUPPORT_TARGET_HUMIDITY == 0

    assert feat & SUPPORT_AUX_HEAT == 0
    assert feat & SUPPORT_PRESET_MODE != 0
    assert feat & SUPPORT_FAN_MODE != 0

    c._zone.heatingOption = True
    with patch.object(system, "has_emergency_heat") as has_emergency_heat:
        has_emergency_heat.return_value = True
        feat = c.supported_features
        assert feat & SUPPORT_AUX_HEAT != 0

    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)
    feat = c1.supported_features
    assert feat != 0
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    feat = c1.supported_features
    assert feat == 0
    feat = c.supported_features
    assert feat != 0


@pytest.mark.asyncio
async def test_target_max_min_humidity(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)

    assert zone.humidityMode == LENNOX_HUMIDITY_MODE_OFF
    assert c.target_humidity is None
    assert c.max_humidity is None
    assert c.min_humidity is None

    c._zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
    assert c.target_humidity == zone.desp
    assert c.max_humidity == zone.maxDehumSp
    assert c.min_humidity == zone.minDehumSp

    c._zone.humidityMode = LENNOX_HUMIDITY_MODE_HUMIDIFY
    assert c.target_humidity == c._zone.husp
    assert c.max_humidity == zone.maxHumSp
    assert c.min_humidity == zone.minHumSp

    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)
    zone1.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
    assert c1.target_humidity == zone1.desp
    assert c1.max_humidity == zone1.maxDehumSp
    assert c1.min_humidity == zone1.minDehumSp
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c1.target_humidity is None
    assert c1.max_humidity is None
    assert c1.min_humidity is None
    assert c.target_humidity == c._zone.husp
    assert c.max_humidity == zone.maxHumSp
    assert c.min_humidity == zone.minHumSp


@pytest.mark.asyncio
async def test_climate_set_humidity(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)

    assert zone.humidityMode == LENNOX_HUMIDITY_MODE_OFF
    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "perform_humidify_setpoint") as perform_humidify_setpoint:
            caplog.clear()
            await c.async_set_humidity(60)
            assert len(caplog.records) == 1
            assert perform_humidify_setpoint.call_count == 0

    zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "perform_humidify_setpoint") as perform_humidify_setpoint:
            caplog.clear()
            await c.async_set_humidity(60)
            assert len(caplog.records) == 0
            assert perform_humidify_setpoint.call_count == 1
            call = perform_humidify_setpoint.mock_calls[0]
            desp = call.kwargs["r_desp"]
            assert desp == 60
            assert "r_husp" not in call.kwargs

    zone.humidityMode = LENNOX_HUMIDITY_MODE_HUMIDIFY
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "perform_humidify_setpoint") as perform_humidify_setpoint:
            caplog.clear()
            await c.async_set_humidity(60)
            assert len(caplog.records) == 0
            assert perform_humidify_setpoint.call_count == 1
            call = perform_humidify_setpoint.mock_calls[0]
            husp = call.kwargs["r_husp"]
            assert husp == 60
            assert "r_desp" not in call.kwargs

    zone1: lennox_zone = system.zone_list[1]
    zone1.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
    c1 = S30Climate(hass, manager, system, zone1)
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        with patch.object(zone1, "perform_humidify_setpoint") as perform_humidify_setpoint:
            caplog.clear()
            await c1.async_set_humidity(60)
            assert len(caplog.records) == 0
            assert perform_humidify_setpoint.call_count == 1
            call = perform_humidify_setpoint.mock_calls[0]
            desp = call.kwargs["r_desp"]
            assert desp == 60
            assert "r_husp" not in call.kwargs
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        with patch.object(zone1, "perform_humidify_setpoint") as perform_humidify_setpoint:
            caplog.clear()
            await c1.async_set_humidity(60)
            assert len(caplog.records) == 1
            assert perform_humidify_setpoint.call_count == 0


@pytest.mark.asyncio
async def test_climate_current_humidity(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert zone.humidityStatus == LENNOX_STATUS_GOOD
    assert c.current_humidity == zone.humidity

    assert zone1.humidityStatus == LENNOX_STATUS_GOOD
    assert c1.current_humidity == zone1.humidity

    # Zoning mode should not change humidity
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert zone.humidityStatus == LENNOX_STATUS_GOOD
    assert c.current_humidity == zone.humidity

    assert zone1.humidityStatus == LENNOX_STATUS_GOOD
    assert c1.current_humidity == zone1.humidity

    system.zoningMode = LENNOX_ZONING_MODE_ZONED

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        zone.humidityStatus = LENNOX_STATUS_NOT_AVAILABLE
        assert c.current_humidity is None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_AVAILABLE in msg

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        zone.humidityStatus = LENNOX_STATUS_NOT_EXIST
        assert c.current_humidity is None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_EXIST in msg


@pytest.mark.asyncio
async def test_climate_current_temperature_f(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert zone.temperatureStatus == LENNOX_STATUS_GOOD
    assert c.current_temperature == zone.temperature
    assert zone1.temperatureStatus == LENNOX_STATUS_GOOD
    assert c1.current_temperature == zone1.temperature

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL

    assert zone.temperatureStatus == LENNOX_STATUS_GOOD
    assert c.current_temperature == zone.temperature
    assert zone1.temperatureStatus == LENNOX_STATUS_GOOD
    assert c1.current_temperature == zone1.temperature

    system.zoningMode = LENNOX_ZONING_MODE_ZONED

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        zone.temperatureStatus = LENNOX_STATUS_NOT_AVAILABLE
        assert c.current_temperature is None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_AVAILABLE in msg

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        zone.temperatureStatus = LENNOX_STATUS_NOT_EXIST
        assert c.current_temperature is None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_EXIST in msg


@pytest.mark.asyncio
async def test_climate_current_temperature_c(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert zone.temperatureStatus == LENNOX_STATUS_GOOD
    assert c.current_temperature == zone.temperatureC
    assert zone1.temperatureStatus == LENNOX_STATUS_GOOD
    assert c1.current_temperature == zone1.temperatureC

    # Should have no affect
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL

    assert zone.temperatureStatus == LENNOX_STATUS_GOOD
    assert c.current_temperature == zone.temperatureC
    assert zone1.temperatureStatus == LENNOX_STATUS_GOOD
    assert c1.current_temperature == zone1.temperatureC

    system.zoningMode = LENNOX_ZONING_MODE_ZONED

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        zone.temperatureStatus = LENNOX_STATUS_NOT_AVAILABLE
        assert c.current_temperature is None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_AVAILABLE in msg

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        zone.temperatureStatus = LENNOX_STATUS_NOT_EXIST
        assert c.current_temperature is None
        assert len(caplog.records) == 1
        msg = caplog.messages[0]
        assert LENNOX_STATUS_NOT_EXIST in msg


@pytest.mark.asyncio
async def test_climate_hvac_mode(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = S30Climate(hass, manager, system, zone1)

    assert c.hvac_mode == HVAC_MODE_HEAT
    assert c1.hvac_mode == HVAC_MODE_COOL

    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.hvac_mode == HVAC_MODE_HEAT_COOL

    zone.systemMode = LENNOX_HVAC_EMERGENCY_HEAT
    assert c.hvac_mode == HVAC_MODE_HEAT

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.hvac_mode == HVAC_MODE_HEAT
    assert c1.hvac_mode is None


@pytest.mark.asyncio
async def test_climate_target_temperature_step(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    zone: lennox_zone = system.zone_list[0]
    c = S30Climate(hass, manager, system, zone)

    assert c.target_temperature_step == 0.5
    manager.is_metric = False
    assert c.target_temperature_step == 1.0


@pytest.mark.asyncio
async def test_climate_hvac_modes(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)

    modes = c.hvac_modes
    assert len(modes) == 4
    assert HVAC_MODE_OFF in modes
    assert HVAC_MODE_HEAT in modes
    assert HVAC_MODE_COOL in modes
    assert HVAC_MODE_HEAT_COOL in modes

    zone.coolingOption = False
    modes = c.hvac_modes
    assert len(modes) == 2
    assert HVAC_MODE_OFF in modes
    assert HVAC_MODE_HEAT in modes

    zone.heatingOption = False
    modes = c.hvac_modes
    assert len(modes) == 1
    assert HVAC_MODE_OFF in modes

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    modes = c.hvac_modes
    assert len(modes) == 0


@pytest.mark.asyncio
async def test_climate_set_hvac_mode(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)

    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_set_hvac_mode(HVAC_MODE_HEAT)
            assert setHVACMode.call_count == 1
            assert setHVACMode.await_args[0][0] == LENNOX_HVAC_HEAT

    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_set_hvac_mode(HVAC_MODE_COOL)
            assert setHVACMode.call_count == 1
            assert setHVACMode.await_args[0][0] == LENNOX_HVAC_COOL

    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_set_hvac_mode(HVAC_MODE_HEAT_COOL)
            assert setHVACMode.call_count == 1
            assert setHVACMode.await_args[0][0] == LENNOX_HVAC_HEAT_COOL

    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_set_hvac_mode(HVAC_MODE_OFF)
            assert setHVACMode.call_count == 1
            assert setHVACMode.await_args[0][0] == LENNOX_HVAC_OFF

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_set_hvac_mode(HVAC_MODE_OFF)
            assert setHVACMode.call_count == 0
            assert len(caplog.records) == 1
            assert "disabled" in caplog.messages[0]


@pytest.mark.asyncio
async def test_climate_hvac_action(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)

    zone.systemMode = LENNOX_HVAC_OFF
    zone.tempOperation = LENNOX_TEMP_OPERATION_OFF
    zone.humOperation = LENNOX_HUMID_OPERATION_OFF
    assert c.hvac_action == "off"

    zone.systemMode = LENNOX_HVAC_COOL
    zone.tempOperation = LENNOX_TEMP_OPERATION_OFF
    zone.humOperation = LENNOX_HUMID_OPERATION_OFF
    assert c.hvac_action == CURRENT_HVAC_IDLE

    zone.systemMode = LENNOX_HVAC_COOL
    zone.tempOperation = LENNOX_TEMP_OPERATION_COOLING
    zone.humOperation = LENNOX_HUMID_OPERATION_OFF
    assert c.hvac_action == LENNOX_TEMP_OPERATION_COOLING

    zone.systemMode = LENNOX_HVAC_COOL
    zone.tempOperation = LENNOX_TEMP_OPERATION_OFF
    zone.humOperation = LENNOX_HUMID_OPERATION_DEHUMID
    assert c.hvac_action == CURRENT_HVAC_DRY

    zone.systemMode = LENNOX_HVAC_COOL
    zone.tempOperation = LENNOX_TEMP_OPERATION_OFF
    zone.humOperation = LENNOX_HUMID_OPERATION_WAITING
    assert c.hvac_action == CURRENT_HVAC_IDLE

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.hvac_action is None


@pytest.mark.asyncio
async def test_climate_preset_modes(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)

    presets = c.preset_modes
    assert PRESET_AWAY in presets
    assert PRESET_CANCEL_HOLD in presets
    assert PRESET_CANCEL_AWAY_MODE in presets
    assert PRESET_NONE in presets
    assert "save energy" in presets
    assert "spring/fall" in presets
    assert "winter" in presets
    assert "summer" in presets
    assert "schedule IQ" in presets
    assert len(presets) == 9

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    presets = c.preset_modes
    assert len(presets) == 0


@pytest.mark.asyncio
async def test_climate_fan_mode(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)
    assert c.fan_mode == "auto"
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.fan_mode is None


@pytest.mark.asyncio
async def test_climate_fan_modes(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)
    modes = c.fan_modes
    assert len(modes) == 3
    assert "auto" in modes
    assert "circulate" in modes
    assert "on" in modes

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    modes = c.fan_modes
    assert len(modes) == 0


@pytest.mark.asyncio
async def test_climate_is_aux_heat(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)
    assert c.is_aux_heat is False
    zone.systemMode = LENNOX_HVAC_EMERGENCY_HEAT
    assert c.is_aux_heat is True
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.is_aux_heat is None


@pytest.mark.asyncio
async def test_climate_turn_aux_heat_on(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)
    zone.systemMode = LENNOX_HVAC_HEAT

    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_turn_aux_heat_on()
            assert setHVACMode.call_count == 1
            assert setHVACMode.await_args[0][0] == LENNOX_HVAC_EMERGENCY_HEAT

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_turn_aux_heat_on()
            assert setHVACMode.call_count == 0
            assert len(caplog.records) == 1
            assert "disabled" in caplog.messages[0]


@pytest.mark.asyncio
async def test_climate_turn_aux_heat_off(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)
    zone.systemMode = LENNOX_HVAC_HEAT

    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_turn_aux_heat_off()
            assert setHVACMode.call_count == 1
            assert setHVACMode.await_args[0][0] == LENNOX_HVAC_HEAT

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setHVACMode") as setHVACMode:
            caplog.clear()
            await c.async_turn_aux_heat_on()
            assert setHVACMode.call_count == 0
            assert len(caplog.records) == 1
            assert "disabled" in caplog.messages[0]


@pytest.mark.asyncio
async def test_climate_set_fan_mode(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)
    zone.systemMode = LENNOX_HVAC_HEAT

    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setFanMode") as setFanMode:
            caplog.clear()
            await c.async_set_fan_mode("circulate")
            assert setFanMode.call_count == 1
            assert setFanMode.await_args[0][0] == "circulate"

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    with caplog.at_level(logging.ERROR):
        with patch.object(zone, "setFanMode") as setFanMode:
            caplog.clear()
            await c.async_set_fan_mode("circulate")
            assert len(caplog.records) == 1
            assert "disabled" in caplog.messages[0]


@pytest.mark.asyncio
async def test_climate_device_info(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id


@pytest.mark.asyncio
async def test_climate_set_temperature(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    zone: lennox_zone = system.zone_list[1]
    c = S30Climate(hass, manager, system, zone)

    with patch.object(lennox_zone, "is_zone_disabled") as is_zone_disabled:
        with caplog.at_level(logging.ERROR):
            caplog.clear()
            is_zone_disabled.return_value = True
            await c.async_set_temperature()
            assert len(caplog.records) == 1
            assert "is disabled" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        await c.async_set_temperature()
        assert len(caplog.records) == 1
        assert "no temperature" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        await c.async_set_temperature(temperature=70, target_temp_high=71)
        assert len(caplog.records) == 1
        assert "provide either temperature or temp_high" in caplog.messages[0]
        assert "70" in caplog.messages[0]
        assert "71" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        await c.async_set_temperature(temperature=70, target_temp_low=68)
        assert len(caplog.records) == 1
        assert "provide either temperature or temp_high" in caplog.messages[0]
        assert "70" in caplog.messages[0]
        assert "68" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        await c.async_set_temperature(target_temp_low=68)
        assert len(caplog.records) == 1
        assert "must provide both temp_high / low" in caplog.messages[0]
        assert "68" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        await c.async_set_temperature(target_temp_high=72)
        assert len(caplog.records) == 1
        assert "must provide both temp_high / low" in caplog.messages[0]
        assert "72" in caplog.messages[0]

    system.single_setpoint_mode = True
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        await c.async_set_temperature(target_temp_high=72, target_temp_low=60)
        assert len(caplog.records) == 1
        assert "zone in single setpoint mode must provide [temperature]" in caplog.messages[0]

    assert manager.is_metric is False
    assert zone.systemMode == "cool"
    assert system.single_setpoint_mode is True
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(hvac_mode="heat", temperature=72)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 1
                assert async_set_hvac_mode.call_args[0][0] == "heat"
                assert perform_setpoint.call_count == 1
                assert perform_setpoint.call_args_list[0].kwargs["r_sp"] == 72

    zone.systemMode = "cool"
    system.single_setpoint_mode = False
    assert manager.is_metric is False
    assert zone.systemMode == "cool"
    assert system.single_setpoint_mode is False
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(hvac_mode="heat", temperature=72)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 1
                assert async_set_hvac_mode.call_args[0][0] == "heat"
                assert perform_setpoint.call_count == 1
                assert perform_setpoint.call_args_list[0].kwargs["r_hsp"] == 72
    zone.systemMode = "heat"
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(hvac_mode="heat", temperature=73)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_hsp"] == 73
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=74)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_hsp"] == 74

    zone.systemMode = None
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=73)
                assert len(caplog.records) == 1
                assert "System Mode is [None]" in caplog.messages[0]

    zone.systemMode = "cool"
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=74)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_csp"] == 74

    zone.systemMode = "off"
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=73)
                assert len(caplog.records) == 1
                assert "System Mode is [off]" in caplog.messages[0]

    zone.systemMode = "cool"
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(target_temp_high=74, target_temp_low=65)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_hsp"] == 65
                assert perform_setpoint.call_args_list[0].kwargs["r_csp"] == 74

    manager.is_metric = True
    zone.systemMode = "cool"
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(target_temp_high=30, target_temp_low=20)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_hspC"] == 20
                assert perform_setpoint.call_args_list[0].kwargs["r_cspC"] == 30

    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=30)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_cspC"] == 30

    zone.systemMode = "heat"
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=20)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_hspC"] == 20

    system.single_setpoint_mode = True
    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=20)
                assert len(caplog.records) == 0
                assert async_set_hvac_mode.call_count == 0
                assert perform_setpoint.call_args_list[0].kwargs["r_spC"] == 20

    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            perform_setpoint.side_effect = S30Exception("this is the error", 20, 10)
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=20)
                assert len(caplog.records) == 1
                assert "this is the error" in caplog.messages[0]

    with patch.object(c, "async_set_hvac_mode") as async_set_hvac_mode:
        with patch.object(zone, "perform_setpoint") as perform_setpoint:
            perform_setpoint.side_effect = ValueError()
            with caplog.at_level(logging.ERROR):
                caplog.clear()
                await c.async_set_temperature(temperature=20)
                assert len(caplog.records) == 1
                assert "unexpected exception" in caplog.messages[0]
