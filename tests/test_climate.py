from lennoxs30api.s30api_async import (
    LENNOX_HVAC_COOL,
    LENNOX_HVAC_HEAT,
    LENNOX_HVAC_HEAT_COOL,
    LENNOX_HVAC_OFF,
    LENNOX_SA_STATE_DISABLED,
    LENNOX_SA_SETPOINT_STATE_AWAY,
    LENNOX_SA_SETPOINT_STATE_TRANSITION,
    LENNOX_SA_SETPOINT_STATE_HOME,
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    lennox_system,
    lennox_zone,
)
from custom_components.lennoxs30 import (
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
    system.sa_setpointState = LENNOX_SA_SETPOINT_STATE_AWAY
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
    system.sa_setpoint_state = LENNOX_SA_SETPOINT_STATE_AWAY
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


@pytest.mark.asyncio
async def test_climate_extra_state_attributes(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)
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


@pytest.mark.asyncio
async def test_supported_features(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)
    feat = c.supported_features
    assert c.is_single_setpoint_active() == True
    assert feat & SUPPORT_TARGET_TEMPERATURE != 0
    assert feat & SUPPORT_TARGET_TEMPERATURE_RANGE == 0

    c._zone._system.single_setpoint_mode = False
    c._zone.systemMode = LENNOX_HVAC_HEAT_COOL
    feat = c.supported_features
    assert c.is_single_setpoint_active() == False
    assert feat & SUPPORT_TARGET_TEMPERATURE == 0
    assert feat & SUPPORT_TARGET_TEMPERATURE_RANGE != 0

    feat = c.supported_features
    assert c._zone.dehumidificationOption == True
    assert c._zone.humidificationOption == False
    assert feat & SUPPORT_TARGET_HUMIDITY != 0

    c._zone.dehumidificationOption = False
    c._zone.humidificationOption = True
    feat = c.supported_features
    assert feat & SUPPORT_TARGET_HUMIDITY != 0

    c._zone.humidificationOption = False
    feat = c.supported_features
    assert feat & SUPPORT_TARGET_HUMIDITY == 0

    assert feat & SUPPORT_AUX_HEAT == 0
    assert feat & SUPPORT_PRESET_MODE != 0
    assert feat & SUPPORT_FAN_MODE != 0


@pytest.mark.asyncio
async def test_target_humidity(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)

    assert zone.humidityMode == LENNOX_HUMIDITY_MODE_OFF
    assert c.target_humidity == None
    assert c.max_humidity == None
    assert c.min_humidity == None

    c._zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
    assert c.target_humidity == zone.desp
    assert c.max_humidity == zone.maxDehumSp
    assert c.min_humidity == zone.minDehumSp

    c._zone.humidityMode = LENNOX_HUMIDITY_MODE_HUMIDIFY
    assert c.target_humidity == c._zone.husp
    assert c.max_humidity == zone.maxHumSp
    assert c.min_humidity == zone.minHumSp


@pytest.mark.asyncio
async def test_set_target_humidity(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    zone: lennox_zone = system._zoneList[0]
    c = S30Climate(hass, manager, system, zone)

    assert zone.humidityMode == LENNOX_HUMIDITY_MODE_OFF
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        with patch.object(
            zone, "perform_humidify_setpoint"
        ) as perform_humidify_setpoint:
            await c.async_set_humidity(60)
            assert len(caplog.records) == 1
            assert perform_humidify_setpoint.call_count == 0

    zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        with patch.object(
            zone, "perform_humidify_setpoint"
        ) as perform_humidify_setpoint:
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
        with patch.object(
            zone, "perform_humidify_setpoint"
        ) as perform_humidify_setpoint:
            await c.async_set_humidity(60)
            assert len(caplog.records) == 0
            assert perform_humidify_setpoint.call_count == 1
            call = perform_humidify_setpoint.mock_calls[0]
            husp = call.kwargs["r_husp"]
            assert husp == 60
            assert "r_desp" not in call.kwargs
