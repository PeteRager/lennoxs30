# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import logging
from unittest.mock import patch
import pytest


from homeassistant.components.climate.const import HVACMode
from homeassistant.exceptions import HomeAssistantError

from lennoxs30api.s30api_async import (
    LENNOX_VENTILATION_MODE_OFF,
    LENNOX_VENTILATION_MODE_ON,
    LENNOX_VENTILATION_MODE_INSTALLER,
    LENNOX_ZONING_MODE_CENTRAL,
    LENNOX_HVAC_OFF,
    LENNOX_HVAC_COOL,
    LENNOX_HVAC_HEAT,
    LENNOX_HVAC_HEAT_COOL,
    LENNOX_HVAC_EMERGENCY_HEAT,
    lennox_system,
    lennox_zone,
)


from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.select import ZoneModeSelect
from custom_components.lennoxs30.const import LENNOX_DOMAIN, UNIQUE_ID_SUFFIX_ZONEMODE_SELECT

from tests.conftest import (
    conf_test_exception_handling,
    conftest_base_entity_availability,
    conf_test_select_info_async_select_option,
)


@pytest.mark.asyncio
async def test_zone_mode_select_mode_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = ZoneModeSelect(hass, manager, system, zone)
    assert c.unique_id == zone.unique_id + UNIQUE_ID_SUFFIX_ZONEMODE_SELECT


@pytest.mark.asyncio
async def test_zone_mode_select_mode_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = ZoneModeSelect(hass, manager, system, zone)
    assert c.name == system.name + "_" + zone.name + "_hvac_mode"

@pytest.mark.parametrize("lennox_mode,ha_mode", 
        [(LENNOX_HVAC_HEAT, HVACMode.HEAT), 
        (LENNOX_HVAC_COOL, HVACMode.COOL),
        (LENNOX_HVAC_HEAT_COOL, HVACMode.HEAT_COOL),
        (LENNOX_HVAC_OFF, HVACMode.OFF),
        (LENNOX_HVAC_EMERGENCY_HEAT,LENNOX_HVAC_EMERGENCY_HEAT),
    ])
@pytest.mark.asyncio
async def test_zone_mode_select_mode_current_option(hass, manager_mz: Manager, lennox_mode:str, ha_mode):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = ZoneModeSelect(hass, manager, system, zone)

    zone.systemMode = lennox_mode
    assert c.current_option == ha_mode


@pytest.mark.asyncio
async def test_zone_mode_select_mode_subscription(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    system.dehumidificationMode = None
    zone: lennox_zone = system.zone_list[0]
    c = ZoneModeSelect(hass, manager, system, zone)
    await c.async_added_to_hass()

    for mode in (LENNOX_HVAC_COOL, LENNOX_HVAC_HEAT, LENNOX_HVAC_EMERGENCY_HEAT, LENNOX_HVAC_OFF):
        with patch.object(c, "schedule_update_ha_state") as update_callback:
            update_set = {"systemMode": mode}
            zone.attr_updater(update_set, "systemMode")
            zone.executeOnUpdateCallbacks()
            assert update_callback.call_count == 1
            assert c.current_option == mode
            assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"systemMode": LENNOX_HVAC_HEAT_COOL}
        zone.attr_updater(update_set, "systemMode")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == HVACMode.HEAT_COOL
        assert c.available is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"zoningMode": LENNOX_ZONING_MODE_CENTRAL}
        system.attr_updater(update_set, "zoningMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.available is True

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_zone_mode_select_mode_options(hass, manager_mz: Manager):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = ZoneModeSelect(hass, manager, system, zone)

    zone.heatingOption = True
    zone.coolingOption = False
    zone.emergencyHeatingOption = False
    opt = c.options
    assert len(opt) == 2
    assert HVACMode.HEAT in opt
    assert HVACMode.OFF in opt

    zone.heatingOption = False
    zone.coolingOption = False
    zone.emergencyHeatingOption = True
    opt = c.options
    assert len(opt) == 2
    assert LENNOX_HVAC_EMERGENCY_HEAT in opt
    assert HVACMode.OFF in opt

    zone.heatingOption = False
    zone.coolingOption = True
    zone.emergencyHeatingOption = False
    opt = c.options
    assert len(opt) == 2
    assert HVACMode.COOL in opt
    assert HVACMode.OFF in opt

    zone.heatingOption = True
    zone.coolingOption = True
    zone.emergencyHeatingOption = False
    opt = c.options
    assert len(opt) == 4
    assert HVACMode.HEAT in opt
    assert HVACMode.HEAT_COOL in opt
    assert HVACMode.COOL in opt
    assert HVACMode.OFF in opt


@pytest.mark.asyncio
async def test_zone_mode_select_mode_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[1]    
    c = ZoneModeSelect(hass, manager, system, zone)

    with patch.object(zone, "setHVACMode") as set_hvac_mode:
        await c.async_select_option(HVACMode.HEAT)
        assert set_hvac_mode.call_count == 1
        set_hvac_mode.assert_called_once_with(LENNOX_HVAC_HEAT)

    with patch.object(zone, "setHVACMode") as set_hvac_mode:
        await c.async_select_option(HVACMode.HEAT_COOL)
        assert set_hvac_mode.call_count == 1
        set_hvac_mode.assert_called_once_with(LENNOX_HVAC_HEAT_COOL)

    await conf_test_exception_handling(
        zone, "setHVACMode", c, c.async_select_option, option=LENNOX_HVAC_HEAT_COOL
    )
    await conf_test_select_info_async_select_option(zone, "setHVACMode", c, caplog)

    with patch.object(zone, "setHVACMode") as set_hvac_mode:
        system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
        with pytest.raises(HomeAssistantError) as hae:
            await c.async_select_option(HVACMode.HEAT_COOL)
        assert set_hvac_mode.call_count == 0
        assert "is disabled" in str(hae.value)

@pytest.mark.asyncio
async def test_zone_mode_select_mode_device_info(hass, manager_mz: Manager):
    manager = manager_mz
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = ZoneModeSelect(hass, manager, system, zone)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id
