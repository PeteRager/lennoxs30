from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_RETRY_WAIT,
    Manager,
)

from custom_components.lennoxs30.const import LENNOX_DOMAIN

import pytest
from custom_components.lennoxs30.switch import (
    S30ManualAwayModeSwitch,
    S30SmartAwayEnableSwitch,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_manual_away_mode_switch_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    c = S30ManualAwayModeSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"manual_away_mode": not system.manualAwayMode}
        system.attr_updater(set, "manual_away_mode", "manualAwayMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False


@pytest.mark.asyncio
async def test_manual_away_mode_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    c = S30ManualAwayModeSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_SW_MA").replace("-", "")
    assert c.name == system.name + "_manual_away_mode"
    assert c.available == True
    assert len(c.extra_state_attributes) == 0
    assert c.update() == True
    assert c.should_poll == False

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()

    system.manualAwayMode = False
    assert c.is_on == False

    system.manualAwayMode = True
    assert c.is_on == True

    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        await c.async_turn_on()
        assert set_manual_away.call_count == 1
        arg0 = set_manual_away.await_args[0][0]
        assert arg0 == True

    with patch.object(system, "set_manual_away_mode") as set_manual_away:
        await c.async_turn_off()
        assert set_manual_away.call_count == 1
        arg0 = set_manual_away.await_args[0][0]
        assert arg0 == False


@pytest.mark.asyncio
async def test_smart_away_enabled_switch_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    c = S30SmartAwayEnableSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"sa_enabled": not system.sa_enabled}
        system.attr_updater(set, "sa_enabled", "sa_enabled")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False


@pytest.mark.asyncio
async def test_smart_away_enabled_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    c = S30SmartAwayEnableSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_SW_SAE").replace("-", "")
    assert c.name == system.name + "_smart_away_enable"
    assert len(c.extra_state_attributes) == 0
    assert c.update() == True
    assert c.should_poll == False

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()

    system.sa_enabled = False
    assert c.is_on == False

    system.sa_enabled = True
    assert c.is_on == True

    with patch.object(system, "enable_smart_away") as enable_smart_away:
        await c.async_turn_on()
        assert enable_smart_away.call_count == 1
        arg0 = enable_smart_away.await_args[0][0]
        assert arg0 == True

    with patch.object(system, "enable_smart_away") as enable_smart_away:
        await c.async_turn_off()
        assert enable_smart_away.call_count == 1
        arg0 = enable_smart_away.await_args[0][0]
        assert arg0 == False
