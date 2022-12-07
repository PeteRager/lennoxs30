# pylint: disable=too-many-lines
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=line-too-long

from unittest.mock import patch
import pytest

from lennoxs30api.s30api_async import lennox_system

from custom_components.lennoxs30 import Manager
from custom_components.lennoxs30.const import LENNOX_DOMAIN
from custom_components.lennoxs30.switch import S30ManualAwayModeSwitch, S30SmartAwayEnableSwitch

from tests.conftest import conf_test_exception_handling, conftest_base_entity_availability


@pytest.mark.asyncio
async def test_manual_away_mode_switch_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    c = S30ManualAwayModeSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"manual_away_mode": not system.manualAwayMode}
        system.attr_updater(update_set, "manual_away_mode", "manualAwayMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_manual_away_mode_switch(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    c = S30ManualAwayModeSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id + "_SW_MA").replace("-", "")
    assert c.name == system.name + "_manual_away_mode"
    assert c.available is True
    assert len(c.extra_state_attributes) == 0
    assert c.update() is True
    assert c.should_poll is False

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    system.manualAwayMode = False
    assert c.is_on is False

    system.manualAwayMode = True
    assert c.is_on is True

    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        await c.async_turn_on()
        assert set_manual_away.call_count == 1
        arg0 = set_manual_away.await_args[0][0]
        assert arg0 is True

    await conf_test_exception_handling(system, "set_manual_away_mode", c, c.async_turn_on)

    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        await c.async_turn_off()
        assert set_manual_away.call_count == 1
        arg0 = set_manual_away.await_args[0][0]
        assert arg0 is False

    await conf_test_exception_handling(system, "set_manual_away_mode", c, c.async_turn_off)


@pytest.mark.asyncio
async def test_smart_away_enabled_switch_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    c = S30SmartAwayEnableSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"sa_enabled": not system.sa_enabled}
        system.attr_updater(update_set, "sa_enabled", "sa_enabled")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    conftest_base_entity_availability(manager, system, c)


@pytest.mark.asyncio
async def test_smart_away_enabled_switch(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    manager.is_metric = False
    c = S30SmartAwayEnableSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id + "_SW_SAE").replace("-", "")
    assert c.name == system.name + "_smart_away_enable"
    assert len(c.extra_state_attributes) == 0
    assert c.update() is True
    assert c.should_poll is False

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    system.sa_enabled = False
    assert c.is_on is False

    system.sa_enabled = True
    assert c.is_on is True

    with patch.object(system, "enable_smart_away") as enable_smart_away:
        await c.async_turn_on()
        assert enable_smart_away.call_count == 1
        arg0 = enable_smart_away.await_args[0][0]
        assert arg0 is True

    await conf_test_exception_handling(system, "enable_smart_away", c, c.async_turn_on)

    with patch.object(system, "enable_smart_away") as enable_smart_away:
        await c.async_turn_off()
        assert enable_smart_away.call_count == 1
        arg0 = enable_smart_away.await_args[0][0]
        assert arg0 is False

    await conf_test_exception_handling(system, "enable_smart_away", c, c.async_turn_off)
