from re import S

from lennoxs30api.s30api_async import (
    LENNOX_HVAC_COOL,
    LENNOX_HVAC_HEAT,
    LENNOX_HVAC_HEAT_COOL,
    LENNOX_HVAC_OFF,
    lennox_system,
    lennox_zone,
)
from custom_components.lennoxs30 import (
    DOMAIN,
    Manager,
)
import pytest
import logging

from custom_components.lennoxs30.climate import S30Climate


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
