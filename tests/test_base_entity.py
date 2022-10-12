from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_LOGIN_FAILED,
    DS_RETRY_WAIT,
    Manager,
)

import pytest
from custom_components.lennoxs30.base_entity import S30BaseEntityMixin
from lennoxs30api import lennox_system


from unittest.mock import patch

from homeassistant.helpers.entity import Entity


# Need to have a derived class the inherits from both in order to have super() call works that need Entity
class TestEntity(S30BaseEntityMixin, Entity):
    def __init__(self, manager: Manager, system: lennox_system):
        super().__init__(manager, system)


@pytest.mark.asyncio
async def test_s30_base_entity_init(hass, manager: Manager, caplog):
    system = manager.api._systemList[0]
    c = TestEntity(manager, system)
    assert c._manager == manager
    assert c._system == system
    assert c.available == True
    assert c.should_poll == False
    assert c.update() == True


@pytest.mark.asyncio
async def test_s30_base_entity_subscription(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    assert manager.connected == True
    c = TestEntity(manager, system)
    await c.async_added_to_hass()

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_RETRY_WAIT)
        assert update_callback.call_count == 1
        assert c.available == False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 1
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 0
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_LOGIN_FAILED)
        assert update_callback.call_count == 1
        assert c.available == False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_LOGIN_FAILED)
        assert update_callback.call_count == 0
        assert c.available == False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        manager.updateState(DS_CONNECTED)
        assert update_callback.call_count == 1
        assert c.available == True
        system.attr_updater({"status": "online"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 2
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        system.attr_updater({"status": "offline"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.available == False

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        system.attr_updater({"status": None}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.available == True

    with patch.object(c, "schedule_update_ha_state") as update_callback:
        system.attr_updater({"status": "otherValue"}, "status", "cloud_status")
        system.executeOnUpdateCallbacks()
        assert update_callback.call_count == 1
        assert c.available == True
