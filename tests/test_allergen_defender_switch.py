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
    S30AllergenDefenderSwitch,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_allergen_defender_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    c = S30AllergenDefenderSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_ADST").replace("-", "")
    assert c.name == system.name + "_allergen_defender"

    attrs = c.extra_state_attributes
    assert len(attrs) == 0

    assert c.update() == True
    assert c.should_poll == False
    assert c.available == True

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()

    system.allergenDefender = True
    assert c.is_on == True

    system.allergenDefender = False
    assert c.is_on == False

    with patch.object(system, "allergenDefender_on") as allergenDefender_on:
        await c.async_turn_on()
        assert allergenDefender_on.call_count == 1

    with patch.object(system, "allergenDefender_off") as allergenDefender_off:
        await c.async_turn_off()
        assert allergenDefender_off.call_count == 1


@pytest.mark.asyncio
async def test_allergen_defender_switch_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    c = S30AllergenDefenderSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"allergenDefender": not system.allergenDefender}
        system.attr_updater(set, "allergenDefender")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.is_on == system.allergenDefender

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False
