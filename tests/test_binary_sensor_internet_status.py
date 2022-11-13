from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    DOMAIN,
    DS_CONNECTED,
    DS_RETRY_WAIT,
    Manager,
)

from custom_components.lennoxs30.const import LENNOX_DOMAIN

import pytest
from custom_components.lennoxs30.binary_sensor import S30InternetStatus

from unittest.mock import patch

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
)


@pytest.mark.asyncio
async def test_internet_status_init(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30InternetStatus(hass, manager, system)
    assert c.unique_id == (system.unique_id() + "_INT_STAT").replace("-", "")
    assert c.extra_state_attributes == {}
    assert c.update() == True
    assert c.should_poll == False
    assert c.name == system.name + "_internet_status"
    assert system.internetStatus == None
    assert c.available == False
    assert c.entity_category == "diagnostic"
    assert c.device_class == DEVICE_CLASS_CONNECTIVITY

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()


@pytest.mark.asyncio
async def test_internet_status_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api.system_list[0]
    c = S30InternetStatus(hass, manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "internetStatus": True,
        }
        system.attr_updater(set, "internetStatus", "internetStatus")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.is_on == True
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "internetStatus": False,
        }
        system.attr_updater(set, "internetStatus", "internetStatus")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.is_on == False
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "internetStatus": None,
        }
        system.attr_updater(set, "internetStatus", "internetStatus")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.available == False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "internetStatus": False,
        }
        system.attr_updater(set, "internetStatus", "internetStatus")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.is_on == False
        assert c.available == True

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
