from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_RETRY_WAIT,
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
    system: lennox_system = manager.api.system_list[0]
    c = S30ZoningSwitch(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {"centralMode": not system.centralMode}
        system.attr_updater(set, "centralMode", "centralMode")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1

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
async def test_zoning_switch(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30ZoningSwitch(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_SW_ZE").replace("-", "")
    assert c.name == system.name + "_zoning_enable"
    assert len(c.extra_state_attributes) == 0
    assert c.update() == True
    assert c.should_poll == False

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
