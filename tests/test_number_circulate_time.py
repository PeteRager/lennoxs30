from lennoxs30api.s30api_async import (
    lennox_system,
    LENNOX_CIRCULATE_TIME_MAX,
    LENNOX_CIRCULATE_TIME_MIN,
)
from custom_components.lennoxs30 import (
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

from unittest.mock import patch


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

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "circulateTime": system.circulateTime + 1.0,
        }
        system.attr_updater(set, "circulateTime")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
