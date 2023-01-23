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
from custom_components.lennoxs30.switch import S30AllergenDefenderSwitch

from tests.conftest import (
    conf_test_exception_handling,
    conftest_base_entity_availability,
    conf_test_switch_info_async_turn_on,
    conf_test_switch_info_async_turn_off,
)


@pytest.mark.asyncio
async def test_allergen_defender_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30AllergenDefenderSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id + "_ADST").replace("-", "")
    assert c.name == system.name + "_allergen_defender"

    attrs = c.extra_state_attributes
    assert len(attrs) == 0

    assert c.update() is True
    assert c.should_poll is False
    assert c.available is True

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id

    system.allergenDefender = True
    assert c.is_on is True

    system.allergenDefender = False
    assert c.is_on is False

    with patch.object(system, "allergenDefender_on") as allergenDefender_on:
        await c.async_turn_on()
        assert allergenDefender_on.call_count == 1

    await conf_test_exception_handling(system, "allergenDefender_on", c, c.async_turn_on)

    with patch.object(system, "allergenDefender_off") as allergenDefender_off:
        await c.async_turn_off()
        assert allergenDefender_off.call_count == 1

    await conf_test_exception_handling(system, "allergenDefender_off", c, c.async_turn_off)
    await conf_test_switch_info_async_turn_off(system, "allergenDefender_off", c, caplog)
    await conf_test_switch_info_async_turn_on(system, "allergenDefender_on", c, caplog)


@pytest.mark.asyncio
async def test_allergen_defender_switch_subscription(hass, manager: Manager):
    system: lennox_system = manager.api.system_list[0]
    c = S30AllergenDefenderSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        update_set = {"allergenDefender": not system.allergenDefender}
        system.attr_updater(update_set, "allergenDefender")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.is_on == system.allergenDefender

    conftest_base_entity_availability(manager, system, c)
