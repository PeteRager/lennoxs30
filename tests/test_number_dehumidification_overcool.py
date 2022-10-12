import logging
from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)
import pytest
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.number import (
    DehumidificationOverCooling,
)

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from unittest.mock import patch

from lennoxs30api.s30exception import S30Exception


@pytest.mark.asyncio
async def test_dehumd_overcool_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    c = DehumidificationOverCooling(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_DOC").replace("-", "")


@pytest.mark.asyncio
async def test_dehumd_overcool_name(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    c = DehumidificationOverCooling(hass, manager, system)

    assert c.name == system.name + "_dehumidification_overcooling"


@pytest.mark.asyncio
async def test_dehumd_overcool_unique_id_unit_of_measure(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)
    assert c.unit_of_measurement == TEMP_CELSIUS
    manager._is_metric = False
    assert c.unit_of_measurement == TEMP_FAHRENHEIT


@pytest.mark.asyncio
async def test_dehumd_overcool_max_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)
    assert c.max_value == system.enhancedDehumidificationOvercoolingC_max
    manager._is_metric = False
    assert c.max_value == system.enhancedDehumidificationOvercoolingF_max


@pytest.mark.asyncio
async def test_dehumd_overcool_min_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)
    assert c.min_value == system.enhancedDehumidificationOvercoolingC_min
    manager._is_metric = False
    assert c.min_value == system.enhancedDehumidificationOvercoolingF_min


@pytest.mark.asyncio
async def test_dehumd_overcool_step(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)
    assert c.step == system.enhancedDehumidificationOvercoolingC_inc
    manager._is_metric = False
    assert c.step == system.enhancedDehumidificationOvercoolingF_inc


@pytest.mark.asyncio
async def test_dehumd_overcool_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)
    assert c.value == system.enhancedDehumidificationOvercoolingC
    manager._is_metric = False
    assert c.value == system.enhancedDehumidificationOvercoolingF


@pytest.mark.asyncio
async def test_dehumd_set_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)

    manager._is_metric = True
    with patch.object(system, "set_enhancedDehumidificationOvercooling") as set_enhancedDehumidificationOvercooling:
        await c.async_set_native_value(2.0)
        assert set_enhancedDehumidificationOvercooling.call_count == 1
        assert set_enhancedDehumidificationOvercooling.call_args.kwargs["r_c"] == 2.0

    manager._is_metric = False
    with patch.object(system, "set_enhancedDehumidificationOvercooling") as set_enhancedDehumidificationOvercooling:
        await c.async_set_native_value(2.0)
        assert set_enhancedDehumidificationOvercooling.call_count == 1
        assert set_enhancedDehumidificationOvercooling.call_args.kwargs["r_f"] == 2.0

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "set_enhancedDehumidificationOvercooling") as set_enhancedDehumidificationOvercooling:
            caplog.clear()
            set_enhancedDehumidificationOvercooling.side_effect = S30Exception("This is the error", 100, 200)
            await c.async_set_native_value(101)
            assert len(caplog.records) == 1
            assert "DehumidificationOverCooling::async_set_native_value" in caplog.messages[0]
            assert "This is the error" in caplog.messages[0]
            assert "101" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "set_enhancedDehumidificationOvercooling") as set_enhancedDehumidificationOvercooling:
            caplog.clear()
            set_enhancedDehumidificationOvercooling.side_effect = Exception("This is the error")
            await c.async_set_native_value(1)
            assert len(caplog.records) == 1
            assert (
                "DehumidificationOverCooling::async_set_native_value unexpected exception - please raise an issue"
                in caplog.messages[0]
            )


@pytest.mark.asyncio
async def test_dehumd_device_info(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()


@pytest.mark.asyncio
async def test_dehumd_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    manager._is_metric = True
    c = DehumidificationOverCooling(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "enhancedDehumidificationOvercoolingC_enable": not system.enhancedDehumidificationOvercoolingC_enable,
            "enhancedDehumidificationOvercoolingF_enable": not system.enhancedDehumidificationOvercoolingF_enable,
            "enhancedDehumidificationOvercoolingC": system.enhancedDehumidificationOvercoolingC + 1,
            "enhancedDehumidificationOvercoolingF": system.enhancedDehumidificationOvercoolingF + 1,
            "enhancedDehumidificationOvercoolingF_min": system.enhancedDehumidificationOvercoolingF_min + 1,
            "enhancedDehumidificationOvercoolingF_max": system.enhancedDehumidificationOvercoolingF_max + 1,
            "enhancedDehumidificationOvercoolingF_inc": 0.5,
            "enhancedDehumidificationOvercoolingC_min": system.enhancedDehumidificationOvercoolingC_min + 1,
            "enhancedDehumidificationOvercoolingC_max": system.enhancedDehumidificationOvercoolingC_max + 1,
            "enhancedDehumidificationOvercoolingC_inc": 1.0,
        }
        system.attr_updater(set, "enhancedDehumidificationOvercoolingC_enable")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        system.attr_updater(set, "enhancedDehumidificationOvercoolingF_enable")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        system.attr_updater(set, "enhancedDehumidificationOvercoolingC")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        system.attr_updater(set, "enhancedDehumidificationOvercoolingF")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 4
        system.attr_updater(set, "enhancedDehumidificationOvercoolingF_min")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 5
        system.attr_updater(set, "enhancedDehumidificationOvercoolingF_max")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 6
        system.attr_updater(set, "enhancedDehumidificationOvercoolingF_inc")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 7
        system.attr_updater(set, "enhancedDehumidificationOvercoolingC_min")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 8
        system.attr_updater(set, "enhancedDehumidificationOvercoolingC_max")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 9
        system.attr_updater(set, "enhancedDehumidificationOvercoolingC_inc")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 10

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
