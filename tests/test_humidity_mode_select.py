import logging
from lennoxs30api.s30api_async import (
    LENNOX_HUMIDITY_MODE_OFF,
    LENNOX_HUMIDITY_MODE_HUMIDIFY,
    LENNOX_HUMIDITY_MODE_DEHUMIDIFY,
    lennox_system,
    lennox_zone,
    LENNOX_ZONING_MODE_CENTRAL,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)
import pytest

from custom_components.lennoxs30.select import (
    HumidityModeSelect,
)

from unittest.mock import patch
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from lennoxs30api.s30exception import S30Exception


@pytest.mark.asyncio
async def test_humidity_mode_select_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    assert c.unique_id == zone.unique_id + "_HMS"


@pytest.mark.asyncio
async def test_humidity_mode_select_name(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    assert c.name == system.name + "_" + zone.name + "_humidity_mode"


@pytest.mark.asyncio
async def test_humidity_mode_select_current_option(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]

    c = HumidityModeSelect(hass, manager, system, zone)
    assert c.current_option == LENNOX_HUMIDITY_MODE_OFF

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        zone.humidityMode = LENNOX_HUMIDITY_MODE_DEHUMIDIFY
        c.zone_update_callback()
        assert c.current_option == LENNOX_HUMIDITY_MODE_DEHUMIDIFY

        zone.humidityMode = LENNOX_HUMIDITY_MODE_HUMIDIFY
        c.zone_update_callback()
        assert c.current_option == LENNOX_HUMIDITY_MODE_HUMIDIFY

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    assert c.current_option == LENNOX_HUMIDITY_MODE_HUMIDIFY


@pytest.mark.asyncio
async def test_humidity_mode_select_current_option_z1(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[1]

    c = HumidityModeSelect(hass, manager, system, zone)
    await c.async_added_to_hass()
    c.entity_id = "select.my_select_zone_1"
    assert c.current_option == LENNOX_HUMIDITY_MODE_OFF
    assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        zone.humidityMode = None
        set = {"humidityMode": LENNOX_HUMIDITY_MODE_DEHUMIDIFY}
        zone.attr_updater(set, "humidityMode")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_HUMIDITY_MODE_DEHUMIDIFY
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"humidityMode": LENNOX_HUMIDITY_MODE_HUMIDIFY}
        zone.attr_updater(set, "humidityMode")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_HUMIDITY_MODE_HUMIDIFY
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"humidityMode": LENNOX_HUMIDITY_MODE_DEHUMIDIFY}
        zone.attr_updater(set, "humidityMode")
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == LENNOX_HUMIDITY_MODE_DEHUMIDIFY

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"zoningMode": LENNOX_ZONING_MODE_CENTRAL}
        system.attr_updater(set, "zoningMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == None
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 1
        assert c.available == True
        system.attr_updater({"status": "online"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        assert c.available == True
        system.attr_updater({"status": "offline"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        assert c.available == False


@pytest.mark.asyncio
async def test_humidity_mode_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = HumidityModeSelect(hass, manager, system, zone1)
    c1.entity_id = "select.my_select_zone_1"

    opt = c.options
    assert len(opt) == 2
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    assert LENNOX_HUMIDITY_MODE_DEHUMIDIFY in opt
    assert zone.dehumidificationOption == True
    assert zone.humidificationOption == False

    zone.humidificationOption = True
    opt = c.options
    assert len(opt) == 3
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    assert LENNOX_HUMIDITY_MODE_DEHUMIDIFY in opt
    assert LENNOX_HUMIDITY_MODE_HUMIDIFY in opt
    assert zone.dehumidificationOption == True

    zone.humidificationOption = False
    zone.dehumidificationOption = False
    opt = c.options
    assert len(opt) == 1
    assert LENNOX_HUMIDITY_MODE_OFF in opt

    opt = c1.options
    assert len(opt) == 2
    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    opt = c.options
    assert len(opt) == 1
    assert LENNOX_HUMIDITY_MODE_OFF in opt
    opt = c1.options
    assert len(opt) == 0


@pytest.mark.asyncio
async def test_humidity_mode_select_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)
    zone1: lennox_zone = system.zone_list[1]
    c1 = HumidityModeSelect(hass, manager, system, zone1)
    c1.entity_id = "select.my_select_zone_1"

    with patch.object(zone, "setHumidityMode") as set_humidity_mode:
        await c.async_select_option(LENNOX_HUMIDITY_MODE_OFF)
        assert set_humidity_mode.call_count == 1
        arg0 = set_humidity_mode.await_args[0][0]
        assert arg0 == LENNOX_HUMIDITY_MODE_OFF

    with patch.object(zone, "setHumidityMode") as set_humidity_mode:
        await c.async_select_option(LENNOX_HUMIDITY_MODE_DEHUMIDIFY)
        assert set_humidity_mode.call_count == 1
        arg0 = set_humidity_mode.await_args[0][0]
        assert arg0 == LENNOX_HUMIDITY_MODE_DEHUMIDIFY

    with patch.object(zone, "setHumidityMode") as set_humidity_mode:
        await c.async_select_option(LENNOX_HUMIDITY_MODE_HUMIDIFY)
        assert set_humidity_mode.call_count == 1
        arg0 = set_humidity_mode.await_args[0][0]
        assert arg0 == LENNOX_HUMIDITY_MODE_HUMIDIFY

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(zone, "setHumidityMode") as set_humidity_mode:
            set_humidity_mode.side_effect = S30Exception("This is the error", 100, 200)
            await c.async_select_option(LENNOX_HUMIDITY_MODE_HUMIDIFY)
            assert set_humidity_mode.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "HumidityModeSelect async_select_option" in msg
            assert "This is the error" in msg

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(zone, "setHumidityMode") as set_humidity_mode:
            set_humidity_mode.side_effect = ValueError("This is the error")
            await c.async_select_option(LENNOX_HUMIDITY_MODE_HUMIDIFY)
            assert set_humidity_mode.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "HumidityModeSelect async_select_option - unexpected exception please raise an issue" in msg

    system.zoningMode = LENNOX_ZONING_MODE_CENTRAL
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(zone1, "setHumidityMode") as set_humidity_mode:
            await c1.async_select_option(LENNOX_HUMIDITY_MODE_DEHUMIDIFY)
            assert set_humidity_mode.call_count == 0
            assert len(caplog.records) == 1
            assert "disabled" in caplog.messages[0]


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_device_info(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    zone: lennox_zone = system.zone_list[0]
    c = HumidityModeSelect(hass, manager, system, zone)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id
