import asyncio
from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)

from custom_components.lennoxs30.const import (
    LENNOX_DOMAIN,
    UNIQUE_ID_SUFFIX_PARAMETER_SAFETY_SWITCH,
)

import pytest
from custom_components.lennoxs30.switch import (
    S30ParameterSafetySwitch,
)

from unittest.mock import patch
from homeassistant.helpers.entity import EntityCategory


@pytest.mark.asyncio
async def test_parameter_safety_switch_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30ParameterSafetySwitch(hass, manager, system)
    await c.async_added_to_hass()

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
async def test_parameter_safety_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30ParameterSafetySwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id + UNIQUE_ID_SUFFIX_PARAMETER_SAFETY_SWITCH).replace("-", "")
    assert c.name == system.name + "_parameter_safety"
    assert len(c.extra_state_attributes) == 0
    assert c.update() == True
    assert c.should_poll == False
    assert c.entity_category == EntityCategory.CONFIG

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    assert c.is_on == True
    manager.parameter_safety_turn_off(system.sysId)
    assert c.is_on == False
    manager.parameter_safety_turn_on(system.sysId)
    assert c.is_on == True


@pytest.mark.asyncio
async def test_parameter_safety_switch_turn_on_off(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30ParameterSafetySwitch(hass, manager, system, 1.0)

    manager.parameter_safety_turn_on(system.sysId)
    manager.parameter_safety_on == True
    assert c.is_on == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        await c.async_turn_off()
        assert update_callback.call_count == 1
        assert c.is_on == False
        await asyncio.sleep(2.0)
        assert update_callback.call_count == 2
        assert c.is_on == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.parameter_safety_turn_off(system.sysId)
        await c.async_turn_on()
        assert update_callback.call_count == 1
        assert c.is_on == True
