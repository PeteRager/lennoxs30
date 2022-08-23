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
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.number import (
    CirculateTime,
)

from homeassistant.const import (
    PERCENTAGE,
)
from lennoxs30api.s30exception import S30Exception

from unittest.mock import patch
import logging


@pytest.mark.asyncio
async def test_circulate_time_unique_id(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = CirculateTime(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_CIRC_TIME").replace("-", "")


@pytest.mark.asyncio
async def test_circulate_time_name(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = CirculateTime(hass, manager, system)

    assert c.name == system.name + "_circulate_time"


@pytest.mark.asyncio
async def test_circulate_time_unit_of_measure(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = CirculateTime(hass, manager, system)
    assert c.unit_of_measurement == PERCENTAGE


@pytest.mark.asyncio
async def test_circulate_time_max_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = CirculateTime(hass, manager, system)
    assert c.max_value == LENNOX_CIRCULATE_TIME_MAX


@pytest.mark.asyncio
async def test_circulate_time_min_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = CirculateTime(hass, manager, system)
    assert c.min_value == LENNOX_CIRCULATE_TIME_MIN


@pytest.mark.asyncio
async def test_circulate_time_step(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = CirculateTime(hass, manager, system)
    assert c.step == 1.0


@pytest.mark.asyncio
async def test_circulate_time_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = True
    c = CirculateTime(hass, manager, system)
    assert c.value == system.circulateTime


@pytest.mark.asyncio
async def test_circulate_time_set_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = True
    c = CirculateTime(hass, manager, system)

    manager._is_metric = True
    with patch.object(system, "set_circulateTime") as set_circulateTime:
        await c.async_set_value(22.0)
        assert set_circulateTime.call_count == 1
        arg0 = set_circulateTime.await_args[0][0]
        assert arg0 == 22.0

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "set_circulateTime") as set_circulateTime:
            caplog.clear()
            set_circulateTime.side_effect = S30Exception("This is the error", 100, 200)
            await c.async_set_value(101)
            assert len(caplog.records) == 1
            assert "CirculateTime::async_set_value" in caplog.messages[0]
            assert "This is the error" in caplog.messages[0]
            assert "101" in caplog.messages[0]

    with caplog.at_level(logging.ERROR):
        with patch.object(system, "set_circulateTime") as set_circulateTime:
            caplog.clear()
            set_circulateTime.side_effect = Exception("This is the error")
            await c.async_set_value(1)
            assert len(caplog.records) == 1
            assert (
                "CirculateTime::async_set_value unexpected exception - please raise an issue"
                in caplog.messages[0]
            )


@pytest.mark.asyncio
async def test_circulate_time_device_info(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = True
    c = CirculateTime(hass, manager, system)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()


@pytest.mark.asyncio
async def test_circulate_time_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = True
    c = CirculateTime(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "circulateTime": system.circulateTime + 1.0,
        }
        system.attr_updater(set, "circulateTime")
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
