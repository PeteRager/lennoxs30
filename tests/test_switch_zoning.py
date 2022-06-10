from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)

from custom_components.lennoxs30.const import LENNOX_DOMAIN

import pytest
from custom_components.lennoxs30.switch import (
    S30ZoningSwitch,
)

from unittest.mock import patch


@pytest.mark.asyncio
async def test_zoning_switch_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = S30ZoningSwitch(hass, manager, system)

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"centralMode": not system.centralMode}
        system.attr_updater(set, "centralMode", "centralMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1


@pytest.mark.asyncio
async def test_zoning_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    c = S30ZoningSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_SW_ZE").replace("-", "")
    assert c.name == system.name + "_zoning_enable"
    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()

    system.centralMode = False
    assert c.is_on == True

    system.centralMode = True
    assert c.is_on == False

    with patch.object(system, "centralMode_off") as centralMode:
        await c.async_turn_on()
        assert centralMode.call_count == 1

    with patch.object(system, "centralMode_on") as centralMode:
        await c.async_turn_off()
        assert centralMode.call_count == 1
