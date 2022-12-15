# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch
import pytest

from homeassistant.const import (
    PERCENTAGE,
)

from lennoxs30api.s30api_async import (
    lennox_system,
    LENNOX_CIRCULATE_TIME_MAX,
    LENNOX_CIRCULATE_TIME_MIN,
)
from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN

from custom_components.lennoxs30.number import (
    CirculateTime,
)

from tests.conftest import conf_test_exception_handling, conftest_base_entity_availability


@pytest.mark.asyncio
async def test_circulate_time_unique_id(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = CirculateTime(hass, manager, system)

    assert c.unique_id == (system.unique_id + "_CIRC_TIME").replace("-", "")


@pytest.mark.asyncio
async def test_circulate_time_name(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = CirculateTime(hass, manager, system)

    assert c.name == system.name + "_circulate_time"


@pytest.mark.asyncio
async def test_circulate_time_unit_of_measure(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = CirculateTime(hass, manager, system)
    assert c.unit_of_measurement == PERCENTAGE


@pytest.mark.asyncio
async def test_circulate_time_max_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = CirculateTime(hass, manager, system)
    assert c.max_value == LENNOX_CIRCULATE_TIME_MAX


@pytest.mark.asyncio
async def test_circulate_time_min_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = CirculateTime(hass, manager, system)
    assert c.min_value == LENNOX_CIRCULATE_TIME_MIN


@pytest.mark.asyncio
async def test_circulate_time_step(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = CirculateTime(hass, manager, system)
    assert c.step == 1.0


@pytest.mark.asyncio
async def test_circulate_time_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = CirculateTime(hass, manager, system)
    assert c.value == system.circulateTime


@pytest.mark.asyncio
async def test_circulate_time_set_value(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = CirculateTime(hass, manager, system)

    manager.is_metric = True
    with patch.object(system, "set_circulateTime") as set_circulateTime:
        await c.async_set_native_value(22.0)
        assert set_circulateTime.call_count == 1
        arg0 = set_circulateTime.await_args[0][0]
        assert arg0 == 22.0

    await conf_test_exception_handling(system, "set_circulateTime", c, c.async_set_native_value, value=101)


@pytest.mark.asyncio
async def test_circulate_time_device_info(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = CirculateTime(hass, manager, system)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id


@pytest.mark.asyncio
async def test_circulate_time_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = True
    c = CirculateTime(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {
            "circulateTime": system.circulateTime + 1.0,
        }
        system.attr_updater(update_set, "circulateTime")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    conftest_base_entity_availability(manager, system, c)
