import logging
from lennoxs30api.s30api_async import (
    LENNOX_DEHUMIDIFICATION_MODE_HIGH,
    LENNOX_DEHUMIDIFICATION_MODE_MEDIUM,
    LENNOX_DEHUMIDIFICATION_MODE_AUTO,
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)
import pytest

from custom_components.lennoxs30.select import (
    DehumidificationModeSelect,
)

from unittest.mock import patch
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from lennoxs30api.s30exception import S30Exception


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)
    assert c.unique_id == system.unique_id() + "_DHMS"


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_name(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)
    assert c.name == system.name + "_dehumidification_mode"


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_current_option(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)

    assert system.dehumidificationMode == LENNOX_DEHUMIDIFICATION_MODE_AUTO
    assert c.current_option == "climate IQ"
    assert c.available == True

    system.dehumidificationMode = LENNOX_DEHUMIDIFICATION_MODE_HIGH
    assert c.current_option == "max"
    assert c.available == True

    system.dehumidificationMode = LENNOX_DEHUMIDIFICATION_MODE_MEDIUM
    assert c.current_option == "normal"
    assert c.available == True

    system.dehumidificationMode = "UNKNOWN MODE"
    assert c.current_option == None
    assert c.available == True


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_subscription(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    system.dehumidificationMode = None
    c = DehumidificationModeSelect(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"dehumidificationMode": LENNOX_DEHUMIDIFICATION_MODE_HIGH}
        system.attr_updater(set, "dehumidificationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == "max"
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"dehumidificationMode": LENNOX_DEHUMIDIFICATION_MODE_MEDIUM}
        system.attr_updater(set, "dehumidificationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == "normal"
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"dehumidificationMode": LENNOX_DEHUMIDIFICATION_MODE_AUTO}
        system.attr_updater(set, "dehumidificationMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.current_option == "climate IQ"
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
async def test_dehumidifier_mode_mode_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)

    opt = c.options
    assert len(opt) == 3
    assert "normal" in opt
    assert "max" in opt
    assert "climate IQ" in opt


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_async_select_options(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)

    with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
        await c.async_select_option("climate IQ")
        assert set_dehumidificationMode.call_count == 1
        arg0 = set_dehumidificationMode.await_args[0][0]
        assert arg0 == LENNOX_DEHUMIDIFICATION_MODE_AUTO

    with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
        await c.async_select_option("max")
        assert set_dehumidificationMode.call_count == 1
        arg0 = set_dehumidificationMode.await_args[0][0]
        assert arg0 == LENNOX_DEHUMIDIFICATION_MODE_HIGH

    with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
        await c.async_select_option("normal")
        assert set_dehumidificationMode.call_count == 1
        arg0 = set_dehumidificationMode.await_args[0][0]
        assert arg0 == LENNOX_DEHUMIDIFICATION_MODE_MEDIUM

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
            await c.async_select_option("bad_value")
            assert set_dehumidificationMode.call_count == 0
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "bad_value" in msg
            assert "max" in msg
            assert "normal" in msg
            assert "climate IQ" in msg

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
            set_dehumidificationMode.side_effect = S30Exception("This is the error", 100, 200)
            await c.async_select_option("normal")
            assert set_dehumidificationMode.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "DehumidificationModeSelect async_select_option" in msg
            assert "This is the error" in msg

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with patch.object(system, "set_dehumidificationMode") as set_dehumidificationMode:
            set_dehumidificationMode.side_effect = ValueError("This is the error")
            await c.async_select_option("normal")
            assert set_dehumidificationMode.call_count == 1
            assert len(caplog.records) == 1
            msg = caplog.messages[0]
            assert "async_select_option unexpected exception please log an issue" in msg


@pytest.mark.asyncio
async def test_dehumidifier_mode_mode_select_device_info(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    await manager.create_devices()
    system: lennox_system = manager.api.system_list[0]
    c = DehumidificationModeSelect(hass, manager, system)

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()
