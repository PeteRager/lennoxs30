from custom_components.lennoxs30 import (
    DS_CONNECTED,
    DS_LOGIN_FAILED,
    DS_RETRY_WAIT,
    Manager,
)

import pytest
from custom_components.lennoxs30.base_entity import S30BaseEntity

from unittest.mock import patch

from homeassistant.helpers.entity import Entity


# Need to have a derived class the inherits from both in order to have super() call works that need Entity
class TestEntity(S30BaseEntity, Entity):
    def __init__(self, manager: Manager):
        super().__init__(manager)


@pytest.mark.asyncio
async def test_s30_base_entity_init(hass, manager: Manager, caplog):
    c = TestEntity(manager)
    assert c._manager == manager
    assert c.available == True
    assert c.should_poll == False
    assert c.update() == True


@pytest.mark.asyncio
async def test_s30_base_entity_subscription(hass, manager: Manager, caplog):
    assert manager.connected == True
    c = TestEntity(manager)
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
