# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

import asyncio
from unittest.mock import patch
import pytest

from homeassistant.helpers.entity import EntityCategory

from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN, UNIQUE_ID_SUFFIX_PARAMETER_SAFETY_SWITCH
from custom_components.lennoxs30.switch import S30ParameterSafetySwitch

from tests.conftest import (
    conftest_base_entity_availability,
    conf_test_switch_info_async_turn_off,
    conf_test_switch_info_async_turn_on,
)


@pytest.mark.asyncio
async def test_parameter_safety_switch_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = S30ParameterSafetySwitch(hass, manager, system)
    await c.async_added_to_hass()

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_parameter_safety_switch(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = S30ParameterSafetySwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id + UNIQUE_ID_SUFFIX_PARAMETER_SAFETY_SWITCH).replace("-", "")
    assert c.name == system.name + "_parameter_safety"
    assert len(c.extra_state_attributes) == 0
    assert c.update() is True
    assert c.should_poll is False
    assert c.entity_category == EntityCategory.CONFIG

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    assert c.is_on is True
    manager.parameter_safety_turn_off(system.sysId)
    assert c.is_on is False
    manager.parameter_safety_turn_on(system.sysId)
    assert c.is_on is True


@pytest.mark.asyncio
async def test_parameter_safety_switch_turn_on_off(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30ParameterSafetySwitch(hass, manager, system, 1.0)

    manager.parameter_safety_turn_on(system.sysId)
    assert c.is_on is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        await c.async_turn_off()
        assert update_callback.call_count == 1
        assert c.is_on is False
        await asyncio.sleep(2.0)
        assert update_callback.call_count == 2
        assert c.is_on is True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.parameter_safety_turn_off(system.sysId)
        await c.async_turn_on()
        assert update_callback.call_count == 1
        assert c.is_on is True

    await conf_test_switch_info_async_turn_off(c, "schedule_update_ha_state", c, caplog)
    await conf_test_switch_info_async_turn_on(c, "schedule_update_ha_state", c, caplog)
