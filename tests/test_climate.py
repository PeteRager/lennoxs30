from re import S
from turtle import up

from lennoxs30api.s30api_async import (
    LENNOX_HVAC_COOL,
    LENNOX_HVAC_HEAT,
    LENNOX_HVAC_HEAT_COOL,
    LENNOX_HVAC_OFF,
    LENNOX_SA_STATE_AWAY,
    LENNOX_SA_STATE_DISABLED,
    lennox_system,
    lennox_zone,
)
from custom_components.lennoxs30 import (
    DOMAIN,
    Manager,
)
import pytest
import logging
import asyncio

from custom_components.lennoxs30.climate import (
    PRESET_CANCEL_AWAY_MODE,
    PRESET_CANCEL_HOLD,
    PRESET_SCHEDULE_OVERRIDE,
    S30Climate,
)

from unittest.mock import patch

from homeassistant.components.climate.const import (
    PRESET_AWAY,
    PRESET_NONE,
)


@pytest.mark.asyncio
async def test_climate_min_max_c(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)

    # Metric Tests
    assert manager._is_metric == True
    zone.systemMode = LENNOX_HVAC_OFF
    assert c.min_temp == None
    assert c.max_temp == None

    zone.systemMode = LENNOX_HVAC_COOL
    assert c.min_temp == zone.minCspC
    assert c.max_temp == zone.maxCspC

    zone.systemMode = LENNOX_HVAC_HEAT
    assert c.min_temp == zone.minHspC
    assert c.max_temp == zone.maxHspC

    assert system.single_setpoint_mode == True
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minCspC
    assert c.max_temp == zone.maxHspC

    system.single_setpoint_mode = False
    assert system.single_setpoint_mode == False
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minHspC
    assert c.max_temp == zone.maxCspC


@pytest.mark.asyncio
async def test_climate_min_max_f(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)
    manager._is_metric = False

    assert manager._is_metric == False
    zone.systemMode = LENNOX_HVAC_OFF
    assert c.min_temp == None
    assert c.max_temp == None

    zone.systemMode = LENNOX_HVAC_COOL
    assert c.min_temp == zone.minCsp
    assert c.max_temp == zone.maxCsp

    zone.systemMode = LENNOX_HVAC_HEAT
    assert c.min_temp == zone.minHsp
    assert c.max_temp == zone.maxHsp

    assert system.single_setpoint_mode == True
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minCsp
    assert c.max_temp == zone.maxHsp

    system.single_setpoint_mode = False
    assert system.single_setpoint_mode == False
    zone.systemMode = LENNOX_HVAC_HEAT_COOL
    assert c.min_temp == zone.minHsp
    assert c.max_temp == zone.maxCsp

    with caplog.at_level(logging.WARNING):
        caplog.clear()
        zone.systemMode = "INVALID_MODE"
        assert c.min_temp == 44.6
        assert c.max_temp == 95
        assert len(caplog.records) == 2


@pytest.mark.asyncio
async def test_climate_system_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "enabled": not system.sa_enabled,
            "reset": not system.sa_reset,
            "cancel": not system.sa_cancel,
            "state": "Cancelled",
            "setpointState": "a setpoint state",
        }
        system.attr_updater(set, "enabled", "sa_enabled")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        system.attr_updater(set, "reset", "sa_reset")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        system.attr_updater(set, "cancel", "sa_cancel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        system.attr_updater(set, "state", "sa_state")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 4
        system.attr_updater(set, "setpointState", "sa_setpointState")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 5


@pytest.mark.asyncio
async def test_climate_preset_mode(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)
    assert system.get_manual_away_mode() == True
    assert c.preset_mode == PRESET_AWAY
    assert c.is_away_mode_on == True
    system.manualAwayMode = False
    assert zone.scheduleId == zone.getManualModeScheduleId()
    assert c.preset_mode == PRESET_NONE
    assert c.is_away_mode_on == False
    system.sa_enabled = True
    assert zone.scheduleId == zone.getManualModeScheduleId()
    assert c.preset_mode == PRESET_NONE
    assert c.is_away_mode_on == False
    system.sa_state = LENNOX_SA_STATE_AWAY
    assert c.preset_mode == PRESET_AWAY
    assert c.is_away_mode_on == True
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert c.preset_mode == PRESET_NONE
    assert c.is_away_mode_on == False
    zone.scheduleId = 2
    assert c.preset_mode == "winter"
    zone.overrideActive = True
    assert c.preset_mode == PRESET_SCHEDULE_OVERRIDE


@pytest.mark.asyncio
async def test_set_preset_mode(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)

    assert system.get_manual_away_mode() == True
    assert system.get_smart_away_mode() == False
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_CANCEL_AWAY_MODE)
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 == False
            assert cancel_smart_away.call_count == 0

    system.sa_enabled = True
    system.sa_state = LENNOX_SA_STATE_AWAY
    assert system.get_manual_away_mode() == True
    assert system.get_smart_away_mode() == True
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_CANCEL_AWAY_MODE)
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 == False
            assert cancel_smart_away.call_count == 1

    system.manualAwayMode = False
    system.sa_enabled = True
    system.sa_state = LENNOX_SA_STATE_AWAY
    assert system.get_manual_away_mode() == False
    assert system.get_smart_away_mode() == True
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_CANCEL_AWAY_MODE)
            assert set_manual_away.call_count == 0
            assert cancel_smart_away.call_count == 1

    system.manualAwayMode = False
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() == False
    assert system.get_smart_away_mode() == False
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(system, "cancel_smart_away") as cancel_smart_away:
            await c.async_set_preset_mode(PRESET_AWAY)
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 == True
            assert cancel_smart_away.call_count == 0

    system.manualAwayMode = True
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() == True
    assert system.get_smart_away_mode() == False
    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        with patch.object(zone, "setSchedule") as zone_set_schedule:
            await c.async_set_preset_mode("winter")
            assert set_manual_away.call_count == 1
            arg0 = set_manual_away.await_args[0][0]
            assert arg0 == False
            assert zone_set_schedule.call_count == 1
            arg0 = zone_set_schedule.await_args[0][0]
            assert arg0 == "winter"

    system.manualAwayMode = False
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() == False
    assert system.get_smart_away_mode() == False
    with patch.object(zone, "setScheduleHold") as zone_set_schedule_hold:
        await c.async_set_preset_mode(PRESET_CANCEL_HOLD)
        assert zone_set_schedule_hold.call_count == 1
        arg0 = zone_set_schedule_hold.await_args[0][0]
        assert arg0 == False

    system.manualAwayMode = False
    system.sa_enabled = False
    system.sa_state = LENNOX_SA_STATE_DISABLED
    assert system.get_manual_away_mode() == False
    assert system.get_smart_away_mode() == False
    with patch.object(zone, "setManualMode") as zone_set_manual_mode:
        await c.async_set_preset_mode(PRESET_NONE)
        assert zone_set_manual_mode.call_count == 1
