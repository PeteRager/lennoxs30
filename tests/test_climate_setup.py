import logging
from lennoxs30api.s30api_async import (
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import MANAGER

from custom_components.lennoxs30.climate import (
    S30Climate,
    async_setup_entry,
)


from unittest.mock import Mock


@pytest.mark.asyncio
async def test_async_setup_entry_mz(hass, manager_mz: Manager, caplog):
    manager = manager_mz
    system: lennox_system = manager._api._systemList[0]
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 4
    for i in range(0, 4):
        assert isinstance(sensor_list[i], S30Climate)
        c: S30Climate = sensor_list[i]
        assert c._zone == system._zoneList[i]


@pytest.mark.asyncio
async def test_async_setup_entry(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 1
    assert isinstance(sensor_list[0], S30Climate)
    c: S30Climate = sensor_list[0]
    assert c._zone == system._zoneList[0]


@pytest.mark.asyncio
async def test_async_setup_entry_no_zones(hass, manager: Manager, caplog):
    system: lennox_system = manager._api._systemList[0]
    system._zoneList = []
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    with caplog.at_level(logging.ERROR):
        caplog.clear()
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)
        assert async_add_entities.called == 0
        assert len(caplog.messages) == 1
        assert "no climate entities" in caplog.messages[0]
