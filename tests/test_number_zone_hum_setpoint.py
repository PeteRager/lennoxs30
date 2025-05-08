"""Tests the zone number humidity setpoint."""
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
from homeassistant.core import HomeAssistant
from lennoxs30api.s30api_async import (
    lennox_system,
)

from custom_components.lennoxs30 import (
    Manager,
)
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.number import (
    HumidifySetpointNumber,
)
from tests.conftest import (
    conf_test_exception_handling,
    conf_test_number_info_async_set_native_value,
    conftest_base_entity_availability,
)


@pytest.mark.asyncio
async def test_zone_hum_unique_id(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)
    assert c.unique_id == (zone.unique_id + "_HUM_SETPOINT").replace("-", "")


@pytest.mark.asyncio
async def test_zone_hum_name(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)

    assert c.name == system.name + "_" + zone.name + "_hum_setpoint"


@pytest.mark.asyncio
async def test_zone_hum_unit_of_measure(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)
    assert c.unit_of_measurement == PERCENTAGE


@pytest.mark.asyncio
async def test_zone_hum_max_value(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)

    assert c.max_value == zone.maxHumSp


@pytest.mark.asyncio
async def test_zone_hum_min_value(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)

    assert c.min_value == zone.minHumSp


@pytest.mark.asyncio
async def test_zone_hum_step(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)
    assert c.step == 1.0


@pytest.mark.asyncio
async def test_zone_hum_value(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)
    assert c.value == zone.husp


@pytest.mark.asyncio
async def test_zone_hum_set_value(hass: HomeAssistant, manager: Manager, caplog: pytest.LogCaptureFixture) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)

    with patch.object(zone, "perform_humidify_setpoint") as perform_humidify_setpoint:
        await c.async_set_native_value(22.0)
        assert perform_humidify_setpoint.call_count == 1
        assert perform_humidify_setpoint.call_args.kwargs["r_husp"]== 22.0

    await conf_test_exception_handling(zone, "perform_humidify_setpoint", c, c.async_set_native_value, value=101)
    await conf_test_number_info_async_set_native_value(zone, "perform_humidify_setpoint", c, caplog)


@pytest.mark.asyncio
async def test_zone_hum_device_info(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == zone.unique_id


@pytest.mark.asyncio
async def test_zone_hum_subscription(hass: HomeAssistant, manager: Manager) -> None:
    system: lennox_system = manager.api.system_list[0]
    zone = system.zone_list[0]
    c = HumidifySetpointNumber(hass, manager, system, zone)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        zone._dirty = True
        zone.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    conftest_base_entity_availability(manager, system, c)
