import logging
from lennoxs30api.s30api_async import (
    lennox_system,
    LENNOX_CIRCULATE_TIME_MAX,
    LENNOX_CIRCULATE_TIME_MIN,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)
import pytest
from custom_components.lennoxs30.const import (
    LENNOX_DOMAIN,
    UNIQUE_ID_SUFFIX_TIMED_VENTILATION_NUMBER,
    VENTILATION_EQUIPMENT_ID,
)

from custom_components.lennoxs30.number import (
    TimedVentilationNumber,
)

from lennoxs30api.s30exception import S30Exception


from homeassistant.const import (
    TIME_MINUTES,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_timed_ventilation_time_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = TimedVentilationNumber(hass, manager, system)
    assert c.unique_id == (system.unique_id() + UNIQUE_ID_SUFFIX_TIMED_VENTILATION_NUMBER).replace("-", "")


@pytest.mark.asyncio
async def test_timed_ventilation_time_name(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = TimedVentilationNumber(hass, manager, system)
    assert c.name == system.name + "_timed_ventilation"


@pytest.mark.asyncio
async def test_timed_ventilation_time_unit_of_measure(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = TimedVentilationNumber(hass, manager, system)
    assert c.unit_of_measurement == TIME_MINUTES


@pytest.mark.asyncio
async def test_timed_ventilation_time_max_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = TimedVentilationNumber(hass, manager, system)
    assert c.max_value == 1440


@pytest.mark.asyncio
async def test_timed_ventilation_time_min_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = TimedVentilationNumber(hass, manager, system)
    assert c.min_value == 0


@pytest.mark.asyncio
async def test_timed_ventilation_time_step(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = TimedVentilationNumber(hass, manager, system)
    assert c.step == 1.0


@pytest.mark.asyncio
async def test_timed_ventilation_time_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = TimedVentilationNumber(hass, manager, system)
    assert c.value == int(system.ventilationRemainingTime / 60)
    system.ventilationRemainingTime = 60
    assert c.value == 1

    system.ventilationRemainingTime = 600
    assert c.value == 10

    system.ventilationRemainingTime = 601
    assert c.value == 10


@pytest.mark.asyncio
async def test_timed_ventilation_time_set_value(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = TimedVentilationNumber(hass, manager, system)

    with patch.object(system, "ventilation_timed") as ventilation_timed:
        await c.async_set_native_value(60.0)
        assert ventilation_timed.call_count == 1
        arg0 = ventilation_timed.await_args[0][0]
        assert arg0 == 3600

    with patch.object(system, "ventilation_timed") as ventilation_timed:
        await c.async_set_native_value(0)
        assert ventilation_timed.call_count == 1
        arg0 = ventilation_timed.await_args[0][0]
        assert arg0 == 0

    with patch.object(system, "ventilation_timed") as ventilation_timed:
        await c.async_set_native_value(1)
        assert ventilation_timed.call_count == 1
        arg0 = ventilation_timed.await_args[0][0]
        assert arg0 == 60
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        await c.async_set_native_value("abc")
        assert len(caplog.records) == 1
        assert "TimedVentilationNumber::async_set_native_value invalid value" in caplog.messages[0]
        assert "abc" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "ventilation_timed") as ventilation_timed:
            caplog.clear()
            ventilation_timed.side_effect = S30Exception("This is the error", 100, 200)
            await c.async_set_native_value(101)
            assert len(caplog.records) == 1
            assert "TimedVentilationNumber::async_set_native_value" in caplog.messages[0]
            assert "This is the error" in caplog.messages[0]
            assert "101" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "ventilation_timed") as ventilation_timed:
            caplog.clear()
            ventilation_timed.side_effect = Exception("This is the error")
            await c.async_set_native_value(1)
            assert len(caplog.records) == 1
            assert (
                "TimedVentilationNumber::async_set_native_value unexpected exception - please raise an issue"
                in caplog.messages[0]
            )


@pytest.mark.asyncio
async def test_timed_ventilation_time_device_info(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    system.ventilationUnitType = "ventilation"
    await manager.create_devices()
    manager.is_metric = True
    c = TimedVentilationNumber(hass, manager, system)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == manager.system_equip_device_map[system.sysId][VENTILATION_EQUIPMENT_ID].unique_name

    system.ventilationUnitType = None
    manager.system_equip_device_map = {}
    await manager.create_devices()
    manager.is_metric = True
    c = TimedVentilationNumber(hass, manager, system)
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        identifiers = c.device_info["identifiers"]
        for x in identifiers:
            assert x[0] == LENNOX_DOMAIN
            assert x[1] == system.unique_id()
        assert len(caplog.records) == 1
        assert "Unable to find" in caplog.messages[0]
        assert str(VENTILATION_EQUIPMENT_ID) in caplog.messages[0]
        assert caplog.records[0].levelname == "WARNING"

    system.ventilationUnitType = None
    manager.system_equip_device_map = {}
    manager.is_metric = True
    c = TimedVentilationNumber(hass, manager, system)
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        identifiers = c.device_info["identifiers"]
        for x in identifiers:
            assert x[0] == LENNOX_DOMAIN
            assert x[1] == system.unique_id()
        assert len(caplog.records) == 1
        assert "No equipment device map found for sysId" in caplog.messages[0]
        assert caplog.records[0].levelname == "ERROR"


@pytest.mark.asyncio
async def test_timed_ventilation_time_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = TimedVentilationNumber(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "ventilationRemainingTime": system.ventilationRemainingTime + 1,
        }
        system.attr_updater(set, "ventilationRemainingTime")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

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
