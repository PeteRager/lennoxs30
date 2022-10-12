import logging
from lennoxs30api.s30api_async import (
    LENNOX_NONE_STR,
    LENNOX_VENTILATION_DAMPER,
    lennox_system,
)
from custom_components.lennoxs30 import (
    Manager,
)
import pytest
from custom_components.lennoxs30.const import CONF_CLOUD_CONNECTION, MANAGER


from unittest.mock import Mock

from custom_components.lennoxs30.binary_sensor import (
    S30HomeStateBinarySensor,
    S30InternetStatus,
    S30RelayServerStatus,
    S30CloudConnectedStatus,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_async_binary_sensor_setup_entry(hass, manager: Manager, caplog):
    system: lennox_system = manager.api._systemList[0]
    entry = manager._config_entry
    hass.data["lennoxs30"] = {}
    hass.data["lennoxs30"][entry.unique_id] = {MANAGER: manager}

    manager.api._isLANConnection = True
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 3
    assert isinstance(sensor_list[0], S30HomeStateBinarySensor)
    assert isinstance(sensor_list[1], S30InternetStatus)
    assert isinstance(sensor_list[2], S30RelayServerStatus)

    manager.api._isLANConnection = False
    async_add_entities = Mock()
    await async_setup_entry(hass, entry, async_add_entities)
    assert async_add_entities.called == 1
    sensor_list = async_add_entities.call_args[0][0]
    assert len(sensor_list) == 2
    assert isinstance(sensor_list[0], S30HomeStateBinarySensor)
    assert isinstance(sensor_list[1], S30CloudConnectedStatus)
