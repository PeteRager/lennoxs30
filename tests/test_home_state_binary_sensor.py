from lennoxs30api.s30api_async import (
    LENNOX_SA_STATE_DISABLED,
    LENNOX_SA_SETPOINT_STATE_HOME,
    LENNOX_SA_SETPOINT_STATE_AWAY,
    LENNOX_SA_STATE_ENABLED_ACTIVE,
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
from custom_components.lennoxs30.binary_sensor import S30HomeStateBinarySensor

from unittest.mock import patch


@pytest.mark.asyncio
async def test_away_mode_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    c = S30HomeStateBinarySensor(hass, manager, system)
    await c.async_added_to_hass()
    assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        set = {
            "enabled": not system.sa_enabled,
            "reset": not system.sa_reset,
            "cancel": not system.sa_cancel,
            "state": "Cancelled",
            "setpointState": "a setpoint state",
        }
        system.attr_updater(set, "enabled", "sa_enabled")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        system.attr_updater(set, "reset", "sa_reset")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        system.attr_updater(set, "cancel", "sa_cancel")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 3
        system.attr_updater(set, "state", "sa_state")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 4
        system.attr_updater(set, "setpointState", "sa_setpointState")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 5

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
async def test_away_mode_value(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    manager._is_metric = False
    c = S30HomeStateBinarySensor(hass, manager, system)

    assert c.unique_id == (system.unique_id() + "_HS").replace("-", "")
    assert c.name == system.name + "_home_state"
    assert c.device_class == "presence"
    assert c.available == True
    assert c.should_poll == False
    assert c.update() == True

    identifiers = c.device_info["identifiers"]
    for x in identifiers:
        assert x[0] == LENNOX_DOMAIN
        assert x[1] == system.unique_id()

    assert c.is_on == False
    attrs = c.extra_state_attributes
    assert attrs["manual_away"] == True
    assert attrs["smart_away"] == False
    assert attrs["smart_away_enabled"] == False
    assert attrs["smart_away_state"] == LENNOX_SA_STATE_DISABLED
    assert attrs["smart_away_reset"] == False
    assert attrs["smart_away_cancel"] == False
    assert attrs["smart_away_setpoint_state"] == LENNOX_SA_SETPOINT_STATE_HOME

    system.manualAwayMode = False
    assert c.is_on == True
    attrs = c.extra_state_attributes
    assert attrs["manual_away"] == False
    assert attrs["smart_away"] == False
    assert attrs["smart_away_enabled"] == False
    assert attrs["smart_away_state"] == LENNOX_SA_STATE_DISABLED
    assert attrs["smart_away_reset"] == False
    assert attrs["smart_away_cancel"] == False
    assert attrs["smart_away_setpoint_state"] == LENNOX_SA_SETPOINT_STATE_HOME

    system.sa_enabled = True
    assert c.is_on == True
    attrs = c.extra_state_attributes
    assert attrs["manual_away"] == False
    assert attrs["smart_away"] == False
    assert attrs["smart_away_enabled"] == True
    assert attrs["smart_away_state"] == LENNOX_SA_STATE_DISABLED
    assert attrs["smart_away_reset"] == False
    assert attrs["smart_away_cancel"] == False
    assert attrs["smart_away_setpoint_state"] == LENNOX_SA_SETPOINT_STATE_HOME

    system.sa_enabled = True
    system.sa_state = LENNOX_SA_STATE_ENABLED_ACTIVE
    system.sa_setpointState = LENNOX_SA_SETPOINT_STATE_AWAY
    assert c.is_on == False
    attrs = c.extra_state_attributes
    assert attrs["manual_away"] == False
    assert attrs["smart_away"] == True
    assert attrs["smart_away_enabled"] == True
    assert attrs["smart_away_state"] == LENNOX_SA_STATE_ENABLED_ACTIVE
    assert attrs["smart_away_reset"] == False
    assert attrs["smart_away_cancel"] == False
    assert attrs["smart_away_setpoint_state"] == LENNOX_SA_SETPOINT_STATE_AWAY
